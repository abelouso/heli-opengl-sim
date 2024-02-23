#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec2

import math
import queue
import inspect
import time
from BaseStateMachine import *

class ApachiHead(BaseStateMachine):

    AT_HEAD_ST = 20
    TURN_KICK_ST = 21
    TURN_LOCK_ST = 22

    NULL_EVT = 20
    NEW_HEAD_EVT = 21
    STOP_EVT = 22
    LOCK_EVT = 23

    STABLE_SPEED = 100.0
    MAX_ROT_SPEED = 10.0
    MAX_ROT_RATE = 2.0
    SPD_DELTA = 2.0
    trg = 0.0
    act = 0.0
    desRotSpd = STABLE_SPEED
    actRotSpd = 0.0
    prevRotSpd = 0.0
    rateSign = 1.0

    rotRate = 0.0
    prevRotRate = 0.0
    rotAccel = 0.0
    RATE_TOL = 0.0001

    NUM_SAMP = 10
    smShare = 1.0 / NUM_SAMP
    lgShare = 1.0 - smShare

    tol = 0.15 #degrees
    alt = 0.0

    eventQ = queue.Queue()
    
    leave = None
    handle = None
    
    dt = 0
    lastStamp = time.time_ns()
    lastChange = lastStamp
    state = AT_HEAD_ST
    firstTick = True
    lastUpdate = time.time_ns()

    def dump(self, source):
        self.db(f"{source:10} ,T: {self.trg: 3.4f}, act: {self.act: 3.4f}, desRS: {self.desRotSpd: 3.4f}, actRotSpd: {self.actRotSpd: 3.4}, rotRate: {self.rotRate: 3.4f}, rotAccel: {self.rotAccel: 3.4f}, elapsed: {self.alt: 3.4f},")

    def newHeadEvt(self):
        # figure out positive or negative kick in the turn
        dh = self.deltaHead()
        dha = abs(dh)
        share = self.kickShare()

        step = share * self.SPD_DELTA
        if dha > self.tol:
            #find the shortest turn
            if ((dh > -180.0 and dh < 0.0) or (dh > 180)):
                self.setRotorSpeed(self.desRotSpd - step)
                self.rateSign = -1.0
            else:
                self.setRotorSpeed(self.desRotSpd + step)
                self.rateSign = 1.0

    def kickHndl(self):
        #TODO: stopped here, make this relaiable turn in the correct direction every time! add slower procceing, better accel numbers
        dh = self.deltaHead()
        rrA = abs(self.rotRate)
        ch = abs(rrA) >= 0.03
        if abs(dh) < self.tol:
            self.db(f" Going to LOCK: {self.trg: 3.4f}, act: {self.act: 3.4f}, dh: {dh: 3.4f}")
            self.sendEvent(self.STOP_EVT)
            self.setRotorSpeed(self.STABLE_SPEED)
        #elif abs(dh) < 1:
        #    self.sendEvent(self.DONE_EVT)
        else:
            if not ch:
                adjRt = self.rateSign * self.rotRate
                adjRtMax = self.rateSign * self.MAX_ROT_RATE
                adj = self.rateSign * self.kickShare()
                self.db(f"In kick hdn: {adjRt: 3.4f}, MAX: {adjRtMax: 3.4f}, step: {adj: 3.4f}, rotRate: {rrA: 3.4f}, ch: {ch}")
                if abs(adjRt < adjRtMax):
                    if  adjRt < 0.2 * self.rateSign * adjRtMax:
                        self.setRotorSpeed(self.desRotSpd + adj)
                    elif adjRt > 0.7 * adjRtMax:
                        self.setRotorSpeed(self.desRotSpd - adj)
                else:
                    if adjRt < -adjRtMax:
                        self.setRotorSpeed(self.desRotSpd + adj)
                    elif adjRt > adjRtMax:
                        self.setRotorSpeed(self.desRotSpd - adj)

    def InTurnLockHndl(self):
        self.setRotorSpeed(self.STABLE_SPEED)

    def lockHndl(self):
        
        chUp = self.rateChanged("up", False)
        chDn = self.rateChanged("dn", True)
        ch = abs(self.rotRate) < 0.0001
        dh = self.deltaHead()
        wt = "Locking it down"
        if abs(dh) < self.tol and ch:
            wt = "Locked in tol, not moving"
            self.sendEvent(self.LOCK_EVT)
        elif abs(dh) < self.tol:
            wt = "In tol, moving"
            self.setRotorSpeed(self.STABLE_SPEED)
        elif abs(dh) > self.tol:
            wt = "OOT"
            if not ch:
                wt += " still, adjusting"
                if self.trg > self.act:
                    self.setRotorSpeed(self.desRotSpd + 0.05 * self.SPD_DELTA)
                    wt += " up"
                else:
                    self.setRotorSpeed(self.desRotSpd - 0.05 * self.SPD_DELTA)
                    wt += " down"
        else:
            if not chDn and self.rotRate > 0.0:
                self.setRotorSpeed(self.desRotSpd - self.SPD_DELTA)
                wt = "constant pos rate kick down"
            elif chDn and self.rotRate < 0.0:
                wt = "varying negative rate, kick up"
                self.setRotorSpeed(self.desRotSpd + self.SPD_DELTA)
        self.db(f"{wt} > chUP: {chUp}, chDn: {chDn}, rt: {self.rotRate: 3.8f}, reqspd: {self.desRotSpd: 3.4f}")
            

    def atHeadHndl(self):
        dh = self.deltaHead()
        self.db(f" dh:  {dh:3.4f}")
        if abs(dh) > (1.5 * self.tol):
            #correct if too far out
            self.newHeadEvt()
            self.sendEvent(self.NEW_HEAD_EVT)
        else:
            chUp = self.rateChanged("up",False)
            chDn = self.rateChanged("dn",False)
            if chUp and self.rotRate > 0.0:
                self.setRotorSpeed(self.desRotSpd - self.SPD_DELTA)
            elif chDn and self.rotRate < 0.0:
                self.setRotorSpeed(self.desRotSpd + self.SPD_DELTA)

    StateHandlers = {
        AT_HEAD_ST: (     None,   atHeadHndl,   None),
        TURN_KICK_ST: (   None,   kickHndl,   None),
        TURN_LOCK_ST: (   InTurnLockHndl,   lockHndl,   None),
    }

    StateMachine = {
        AT_HEAD_ST: {
            NEW_HEAD_EVT: (TURN_KICK_ST, newHeadEvt),
            STOP_EVT: (TURN_LOCK_ST, None),
            LOCK_EVT: (AT_HEAD_ST, None),
            NULL_EVT: (AT_HEAD_ST, None),
        },
        TURN_KICK_ST: {
            NEW_HEAD_EVT: (TURN_KICK_ST, newHeadEvt),
            STOP_EVT: (TURN_LOCK_ST, None),
            LOCK_EVT: (AT_HEAD_ST, None),
            NULL_EVT: (TURN_KICK_ST, None),
        },
        TURN_LOCK_ST: {
            NEW_HEAD_EVT: (TURN_KICK_ST, newHeadEvt),
            STOP_EVT: (TURN_LOCK_ST, None),
            LOCK_EVT: (AT_HEAD_ST, None),
            NULL_EVT: (TURN_LOCK_ST, None),
        },
    }


    def __init__(self):
        super().__init__("ApachiHead", 0x4)
        self.state = self.AT_HEAD_ST

    def tick(self, act, spd, dt, alt):
        self.updateTimeStamp()
        self.actRotSpd = spd
        self.alt = alt
        self.updateActRotRate(act)
        if abs(self.desRotSpd - self.actRotSpd) > 0.001 or not self.alt > 1.0:
            self.dump("WAIT")
        else:
            self.dump("TICK")
            if self.handle is not None:
                self.handle(self)
        self.next()
        self.lastChange = time.time_ns()
        self.act = act
        return self.desRotSpd

    def updateActRotRate(self,act):
        now = time.time_ns()
        deltaT = now - self.lastUpdate
        if (deltaT) > 90.0e6: #ms
            self.dt = (deltaT ) * 0.00000001
            rotRate = (act - self.act) / self.dt
            if abs(rotRate - self.rotRate) > 4: #to account large swings in rotation rate changes
                rotRate = self.rotRate
            rotRatAvg = self.rotRate * self.lgShare + rotRate * self.smShare
            accel = (rotRatAvg - self.rotRate) / self.dt
            #self.db(f" act: {act:3.4f}, prev act: {self.act}, dt: {self.dt}, instRot: {rotRate:3.4f}, avg: {rotRatAvg:3.4f}, lgShare: {self.lgShare:3.4f}, smShare: {self.smShare:3.4f}")
            self.rotAccel = self.rotAccel * self.lgShare + accel * self.smShare
            self.rotRate = rotRatAvg
            self.lastUpdate = now

    def setHeading(self, heading):
        self.db(f" ============================================= Requested heading: {heading: 3.4f}")
        if heading < 0.0:
            heading = 360.0 + heading
        if abs(heading - self.act) > self.tol:
            self.trg = heading
            self.sendEvent(self.NEW_HEAD_EVT)
            self.dump("SET HDG")
        self.db(f" ============================================= Set heading: {self.trg: 3.4f}")

    def deltaHead(self):
        return self.trg - self.act
    
    def setRotorSpeed(self, spd):
        self.desRotSpd = spd
        self.lastChange = time.time_ns()
        self.prevRotRate = self.rotRate
        self.dump("CHG ROT SPD")

    def rateChanged(self,dir, update = True):
        drA = abs(self.prevRotRate - self.rotRate)
        if dir == "up":
            res = (self.rotRate > self.prevRotRate and drA > self.RATE_TOL)
        elif dir == "dn":
            res = (self.rotRate < self.prevRotRate and drA > self.RATE_TOL)
        else:
            res = (self.rotRate > self.prevRotRate and drA > self.RATE_TOL) or (self.rotRate < self.prevRotRate and drA > self.RATE_TOL)
        if update: self.prevRotRate = self.prevRotRate
        return res

    def isStable(self):
        stable = abs(self.rotRate) < 0.01 and abs(self.actRotSpd - self.STABLE_SPEED) <= 0.13
        return stable

    def kickShare(self):
        tRad = math.radians(self.trg)
        aRad = math.radians(self.act)
        trVec = Vec2(math.sin(tRad), math.cos(tRad))
        aVec = Vec2(math.sin(aRad), math.cos(aRad))
        dot = trVec.dot(aVec)
        #1 - codirectional
        #0 - +/- 90
        #-1 180 (opposit)
        share = 0.2 * ((1.0 - (dot + 0.0)) / 2.0)
        return share