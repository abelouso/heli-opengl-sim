#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode


import math
import queue

from BaseObject import *
from StigChopper import *

class AltHold():
    ON_GND_ST = 0
    UP_ST = 1
    DOWN_ST = 3
    AT_ALT_ST = 4
    NULL_EVT = 0
    DONE_EVT = 1
    FALL_EVT = 2
    RAISE_EVT = 3
    
    MAX_ALT_RATE = 5

    handle = None
    leave = None

    def lndHndl(self):
        da = self.getDeltaAlt()
        if math.fabs(da) > self.tol:
            dSpd = self.calcDeltaSpd(da)
            self.setMainRotorSpeed(self.rotSpd + dSpd)
            print(f"new rotor spd: {self.rotSpd}")

    def gndHndl(self):
        da = self.getDeltaAlt()
        if da > 0.0:
            self.sendEvent(self.RAISE_EVT)
        elif math.fabs(da) < self.tol:
            self.sendEvent(self.DONE_EVT)


    def upHndl(self):

        da = self.getDeltaAlt()
        if math.fabs(da) <= self.tol:
            print("===================== ACCENDED TO ALT, go to AT ALT =====================")
            self.correctRate = True
            self.sendEvent(self.DONE_EVT)
            self.prevAltRate = self.altRate
        else:
            if math.fabs(self.rotSpd - self.actMainSpd) > 0.001:
                print(f"UpHndl Rotor spinning up/down: req: {self.rotSpd}, actual {self.actMainSpd}, rate: {self.altRate}, alt: {self.act}")
                return
            
            if math.fabs(da) > self.tol and da < 0.0:
                self.sendEvent(self.FALL_EVT)
            elif da > 0.0:
                share = 0.17 * self.MAX_ALT_RATE
                #still raising slow down the raise the closer we get
                print(f"upHndl: Raising: {self.trg} vs {self.act}, rate: {self.altRate} spd: {self.rotSpd}, act spd: {self.actMainSpd}")
                if self.altRate >= self.MAX_ALT_RATE:
                    print(f"upHndl: Above Max rate")
                    #if (self.prevAltRate is not None and self.prevAltRate > self.altRate) or self.prevAltRate is None:
                    if self.correctRate:
                        self.setMainRotorSpeed(self.rotSpd * share)
                        self.correctRate = False
                        print(f"upHndl: command lower speed {self.rotSpd}")
                elif self.altRate <= 0.0 and self.takeOfRotorSpeed is not None:
                    print(f"upHndl: Rate is negative, spinning up...")
                    self.setMainRotorSpeed(0.94 * 400)
                    self.correctRate = True
                elif self.altRate == 0.0:
                    self.setMainRotorSpeed(self.rotSpd + 20)

    def inFallHndl(self):
        dSpd = self.calcDeltaSpd(self.getDeltaAlt())
        self.setMainRotorSpeed(self.rotSpd + dSpd)

    def downHndl(self):
        
        da = self.getDeltaAlt()
        
        if math.fabs(da) <= self.tol:
            print("===================== DECENDED TO ALT, go to AT ALT =====================")
            self.correctRate = True
            self.sendEvent(self.DONE_EVT)
            self.prevAltRate = self.altRate
        else:
            if math.fabs(self.rotSpd - self.actMainSpd) > 0.001:
                print(f"downHndl: Rotor spinning up/down: req: {self.rotSpd}, actual {self.actMainSpd}, rate: {self.altRate}, alt: {self.act}")
                return
            da = self.getDeltaAlt()
            if math.fabs(da) > self.tol and da > 0.0:
                self.sendEvent(self.RAISE_EVT)
            elif da < 0.0:
                share = 1.16
                #still raising slow down the raise the closer we get
                print(f"donwHndl: Falling: {self.trg} vs {self.act}, rate: {self.altRate} , spd: {self.rotSpd}, act spd: {self.actMainSpd}")
                if self.altRate < -self.MAX_ALT_RATE:
                    print(f"downHndl: Below Min rate")
                    if self.correctRate:
                        self.setMainRotorSpeed(self.rotSpd * share)
                        self.correctRate = False
                        print(f"downHndl: commanded higher speed")
                elif self.altRate >= 0.0 and self.takeOfRotorSpeed is not None:
                    self.setMainRotorSpeed(0.89 * self.takeOfRotorSpeed)
                    self.correctRate = True
                elif self.altRate == 0.0:
                    #if we are howevering, start decending...
                    self.setMainRotorSpeed(self.rotSpd - 20)

    def atAltHndl(self):
        
        if math.fabs(self.rotSpd - self.actMainSpd) > 0.001:
            print(f"atAltHndl: Rotor spinning up/down: req: {self.rotSpd}, actual {self.actMainSpd}, rate: {self.altRate}, alt: {self.act}")
            return
        
        da = self.getDeltaAlt()
        if math.fabs(da) > self.tol:
            if da > 0.0:
                print(f"atAltHndl:MUST ASCEND: {self.trg} vs {self.act}, spd: {self.rotSpd}")
                self.sendEvent(self.RAISE_EVT)
                pass
            elif da < 0.0:
                #still raising slow down the raise the closer we get
                print(f"atAltHndl:MUST DECENT: {self.trg} vs {self.act}, spd: {self.rotSpd}")
                self.sendEvent(self.FALL_EVT)
                pass
        else:
            actingRate = 1.0
            share = 0.155
            ds = share * math.fabs(self.rotSpd)
            newSpd = self.rotSpd
            if self.altRate > actingRate and self.correctRate: 
                #need to bring rate down
                newSpd = self.rotSpd - ds
                self.correctRate = False
                self.prevAltRate = self.altRate
                print(f"Slowed down rotor speed to {newSpd}")
            elif self.altRate < -actingRate and self.correctRate:
                #need to bring rate up
                newSpd = self.rotSpd + ds
                self.correctRate = False
                self.prevAltRate = self.altRate
                print(f"Sped up rotor speed to {newSpd}")
            if (self.prevAltRate < 0.0 and self.altRate > 0.0) or (self.prevAltRate > 0.0 and self.altRate < 0.0):
                #sign change, correct again
                print(f"Sign change, correcting again")
                self.correctRate = True
            self.setMainRotorSpeed(newSpd)
            print(f"At Alt - hovering: alt: {self.act} rate {self.altRate}, spd: actual {self.actMainSpd}, req: {self.rotSpd}")

    stateMachine = {
        ON_GND_ST : {
                    NULL_EVT : (ON_GND_ST,lndHndl,gndHndl,None),
                    DONE_EVT : (AT_ALT_ST,None,atAltHndl,None), 
                    RAISE_EVT: (UP_ST,None,upHndl,None), 
                    FALL_EVT: (DOWN_ST,inFallHndl,downHndl,None) },
        UP_ST : {
                    NULL_EVT: (UP_ST,None,upHndl,None),
                    DONE_EVT: (AT_ALT_ST,None,atAltHndl,None),
                    RAISE_EVT: (UP_ST,lndHndl,upHndl,None),
                    FALL_EVT: (DOWN_ST,inFallHndl,downHndl,None) },
        DOWN_ST : {
                    NULL_EVT: (DOWN_ST,None,downHndl,None),
                    DONE_EVT: (AT_ALT_ST,None,atAltHndl,None),
                    RAISE_EVT: (UP_ST,lndHndl,upHndl,None),
                    FALL_EVT: (DOWN_ST,inFallHndl,downHndl,None) },
        AT_ALT_ST : {
                    NULL_EVT: (AT_ALT_ST,None,atAltHndl,None),
                    DONE_EVT: (AT_ALT_ST,None,atAltHndl,None),
                    RAISE_EVT: (UP_ST,lndHndl,upHndl,None),
                    FALL_EVT: (DOWN_ST,inFallHndl,downHndl,None) },
    }
    def __init__(self):
        self.state = self.ON_GND_ST
        self.trg = 0
        self.act = 0
        self.setMainRotorSpeed(0)
        self.diff = 0.25
        self.tol = 2.0
        self.spCoeff = 0.5
        self.prevAct = None
        self.maxDeltaSpd = 10
        self.eventQ = queue.Queue()
        self.leave = None
        self.firstTick = True
        self.dt = None
        self.altAccel = 0.0
        self.altRate = 0.0
        self.actMainSpd = 0.0
        self.takeOfRotorSpeed = None
        self.prevAltRate = None
        self.correctRate = True

    def next(self):
        while not self.eventQ.empty():
            evt = self.eventQ.get()
            stMap = self.stateMachine[self.state]
            newState = self.state
            if evt in stMap:
                newState, enter, handle, leave = stMap[evt]
                if newState != self.state or self.firstTick:
                    if self.leave is not None:
                        self.leave()
                    self.leave = leave
                    if enter is not None:
                        enter(self)
                else:
                    pass
                if handle is not None:
                    handle(self)
                self.handle = handle
                self.firstTick = False
                
    def sendEvent(self,evt):
        self.eventQ.put(evt)

    def tick(self,act, spd, dt):
        self.dt = dt
        ##TODO: provide service for thisin heli main
        self.actMainSpd = spd
        altRate = (act - self.act) / self.dt
        if math.fabs(altRate - self.altRate) > 5:
            altRate = self.altRate
        self.altAccel = (altRate - self.altRate) / self.dt
        self.altRate = altRate
        self.act = act
        if self.takeOfRotorSpeed is None and self.act > 0.0:
            self.takeOfRotorSpeed = self.rotSpd
        if self.handle is not None:
            self.handle(self)
        self.next()
        return self.rotSpd
    
    def getDeltaAlt(self):
        da = self.trg - self.act
        return da
    
    def calcDeltaSpd(self,da):
        dSpd = self.spCoeff * da * self.diff * (math.exp(2) - 1.0)
        print(f"calcDeltaSpd: Correction: rate: {self.altRate}, act {self.act}, trg: {self.trg}, spd: {self.rotSpd}, dAlt {da}, dSpd: {dSpd}, new speed {self.rotSpd + dSpd}")
        return dSpd

    def calcKick(self, curRate, desRate, curSpd):
        pass

    def setTarget(self,trg):
        self.trg = trg

    def rotorSpeed(self):
        return self.rotSpd
    
    def setMainRotorSpeed(self,spd):
        if spd >= 0.0 and spd <= 400.0:
            self.rotSpd = spd


class Apachi(StigChopper):
    def __init__(self,id, pos, scale=0.2):
        StigChopper.__init__(self,id,pos,"Models/ArmyCopter", {}, "apachi")
        self.actor.setScale(scale,scale,scale)
        self.rotDir = 1.0
        self.actAngle = 0
        self.mainSpeed = 0.0
        self.tilt = 0.0
        self.tailSpeed = 0.0
        self.altCtrl = AltHold()
        self.altCtrl.trg = 70
        self.altCtrl.sendEvent(self.altCtrl.NULL_EVT)
        #self.m_fuelCapacity = 100

    def update(self,dt,tick):
        StigChopper.update(self,dt,tick)

        '''
        self.actAngle += 1
        if (abs(self.actAngle) > 3600):
            self.rotDir *= -1.0
            self.actAngle = 0

        angDeg = tick * 9.0
        angRad = math.radians(angDeg)
        radius = 39 + 2.2 * self.id
        if True:
            self.actor.setPos(radius * math.sin(angRad), -radius * math.cos(angRad), 70)
        else:
            self.actor.setPos(radius * math.cos(angRad), -radius * math.sin(angRad), 70)
        self.actor.setHpr(angDeg - 90.0,-5,-15)
        '''


    def runLogic(self,dt,tick):
        StigChopper.runLogic(self,dt,tick)
        pos = base.gps(self.id)
        alt = pos.getZ()
        self.tailSpeed = 100.0
        #TODO: provide access to this
        actSpd = base.myChoppers[self.id][1].actMainRotorSpeed_RPM
        self.mainSpeed = self.altCtrl.tick(alt,actSpd,dt)

        base.requestSettings(self.id,self.mainSpeed,self.tilt,self.tailSpeed)


if __name__ == '__main__':
    print("Starting....")
    alt = AltHold()
    alt.sendEvent(alt.NULL_EVT)
    alt.tick(20,100)
    alt.tick(20,alt.rotorSpeed())