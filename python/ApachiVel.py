#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2

import math
import queue
import inspect
import time
from BaseStateMachine import *

class ApachiVel(BaseStateMachine):

    MAINT_ST = 30
    CHANGE_ST = 31
    SIDE_ST = 32

    NULL_EVT = 30
    ACCEL_EVT = 31
    AT_SPEED_EVT = 32
    STOP_EVT = 33
    SIDE_EVT = 34
    FWD_EVT = 35


    TILT_STEP = 0.1
    MAX_SPEED = 1.0
    MAX_TILT = 4.0
    MAX_ACCEL = 0.001
    SPEED_CH_TOL = 0.00002
    speed = 0.0
    prevSpeed = 0.0
    trg = 0.0
    actPos = Vec3(0,0,0)
    lstPos = Vec3(0,0,0)

    desTilt = 0.0
    actTilt = 0.0
    prevTilt = 0.0

    accel = 0.0

    tol = 0.005
    alt = 0.0
    

    NUM_SAMP = 10
    smShare = 1.0 / NUM_SAMP
    lgShare = 1.0 - smShare

    eventQ = queue.Queue()
    leave = None
    handle = None
    
    dt = 0
    lastStamp = time.time_ns()
    lastChange = lastStamp
    state = MAINT_ST
    firstTick = True
    facing = 0.0
    lastUpdate = time.time_ns()

    def dump(self, source):
        pDiff = self.pDiffN()
        cp = self.actPos
        lp = self.lstPos
        self.db(f"{source:10},T: {self.trg: 3.4f}, velspd: {self.speed: 3.6f}, "\
                f"desT: {self.desTilt: 3.4f}, velactT: {self.actTilt: 3.6f}, velaccel: {self.accel: 3.9f}, "\
                f"facing: {self.facing: 3.4f}, moving: {self.velocityHeading: 3.4f} "\
                f"lp: ({lp.x: 3.4f},{lp.y: 3.4f},{lp.z: 3.4f}), cp: ({cp.x: 3.4f},{cp.y: 3.4f},{cp.z: 3.4f}) "\
                f"dir: ({pDiff.x: 3.4f},{pDiff.y: 3.4f},{pDiff.z: 3.4f})")

    def stopEvt(self):
        self.setTilt(0.0)

    def maintHndl(self):
        
        dV = self.delta()
        self.db(f" delta V: {dV:3.4f}")
        if not self.isAlongPath():
            self.sendEvent(self.SIDE_EVT)
        elif abs(dV) > self.tol:
            self.db(f" transition to ACCEL ST")
            self.sendEvent(self.ACCEL_EVT)

    def changeHndl(self):
        dV = self.delta()
        dva = abs(dV)
        wh = "Handling speed change: "
        reqTilt = 0.0
        SM_STEP = 0.0015 * self.MAX_TILT
        '''
        if dva < self.tol:
            #self.sendEvent(self.AT_SPEED_EVT)
            pass
        '''
        if not self.isAlongPath():
            self.sendEvent(self.SIDE_EVT)
            wh = "not along axis"
        else:
            chUp = self.speedChanged("up",False)
            chDn = self.speedChanged("dn",True)
            wh = "Noting to correct"
            if self.speed > self.MAX_SPEED and self.accel > 0.0:
                wh = "above high limit, zeroed out"
                self.setTilt(0.0)
            elif self.speed < -self.MAX_SPEED and self.accel < 0.0:
                wh = "below low limit, zeroed out"
                self.setTilt(0.0)
            elif self.speed < (self.trg - self.tol):
                #accelerating
                wh = "spd below lower tol"
                if self.accel <= 0.0:
                    #self.setTilt(self.desTilt + self.TILT_STEP * abs(dV) / self.MAX_SPEED)
                    reqTilt = self.MAX_TILT * dva / self.MAX_SPEED
                    self.setTilt(reqTilt)
                    wh += " kicked up"
                elif abs(self.accel) <= self.MAX_ACCEL:
                    wh += " decel kick down"
                    reqTilt = self.desTilt + SM_STEP
                    self.setTilt(reqTilt)
            elif self.speed > (self.trg + self.tol):
                #decelerating
                wh = "speed above higher tol"
                if self.accel >= 0.0:
                    #self.setTilt(self.desTilt - self.TILT_STEP * abs(dV) / self.MAX_SPEED)
                    reqTilt = -self.MAX_TILT * dva / self.MAX_SPEED
                    self.setTilt(reqTilt)
                    wh += " kicked down"
                elif abs(self.accel) <= self.MAX_ACCEL: 
                    wh += " accel kick up"
                    reqTilt = self.desTilt - SM_STEP
                    self.setTilt(reqTilt)

            elif dva <= self.tol:
                wh = "in tol "
                if self.accel > 0.0:
                    wh += "accel "
                    if self.speed > self.trg:
                        wh += "above target, kick donw"
                        reqTilt = -SM_STEP
                        self.setTilt(reqTilt)
                    else:
                        wh += "below target, ok"
                else:
                    wh += "decel "
                    if self.speed < self.trg:
                        wh += "below target, kick up"
                        reqTilt = SM_STEP
                        self.setTilt(reqTilt)
                    else:
                        wh += "above target, ok"
                        
            '''
            elif dva <= self.tol and abs(self.accel) < 0.00001:
                wh = "about at the right speed"
                self.setTilt(0.0)
            '''
        self.db(f"{wh} > speed: {self.speed: 3.4f}, dV: {dV:3.4f}, acc: {self.accel: 3.6f},tilt: {self.desTilt: 3.4f}, step: {reqTilt: 3.4f}")

    def sideHndl(self):
        if self.isAlongPath() and abs(self.accel) < 0.00001:
            self.db(f"Moving forward again...")
            self.sendEvent(self.FWD_EVT)
        else:
            self.db("Moving sideways, setting tilt to 0.0, drifting")
            self.setTilt(0.0)
            self.setSpeed(0.0)
                    

    StateHandlers = {
        MAINT_ST: (     None,   maintHndl,   None),
        CHANGE_ST: (   None,   changeHndl,   None),
        SIDE_ST: (   None,   sideHndl,   None),
    }

    StateMachine = {
        MAINT_ST: {
            ACCEL_EVT: (CHANGE_ST, None),
            STOP_EVT: (MAINT_ST, stopEvt),
            AT_SPEED_EVT: (MAINT_ST, None),
            NULL_EVT: (MAINT_ST, None),
            SIDE_EVT: (SIDE_ST, None),
        },
        CHANGE_ST: {
            ACCEL_EVT: (CHANGE_ST, None),
            STOP_EVT: (MAINT_ST, stopEvt),
            AT_SPEED_EVT: (MAINT_ST, None),
            NULL_EVT: (CHANGE_ST, None),
            SIDE_EVT: (SIDE_ST, None),
        },
        SIDE_ST: {
            FWD_EVT: (MAINT_ST, None),
        },
    }

    def __init__(self):
        super().__init__("ApachiVel",0x8)
        self.state = self.MAINT_ST
        self.velocityHeading = 0.0
        self.lstPos = self.actPos

    def tick(self, actPos, tilt, dt, alt, facing):
        self.updateTimeStamp()
        self.alt = alt
        pos3d = Vec3(actPos.getX(), actPos.getY(), actPos.getZ())
        self.actTilt = tilt
        self.updateSpeed(pos3d)
        self.facing = facing
        if abs(self.desTilt - self.actTilt) > 0.0001 or (alt < 1.0):
            self.dump("WAIT")
        else:
            self.dump("TICK")
            if self.handle is not None:
                self.handle(self)
        self.next()
        self.lastChange = time.time_ns()
        return self.desTilt
    
    def updateSpeed(self, actPos):
        if self.alt > 0.0:
            now = time.time_ns()
            deltaT = now - self.lastUpdate
            if (deltaT) > 80.0e6: #ms
                self.dt = (deltaT ) * 0.00000001
                p1 = actPos.xy
                p2 = self.actPos.xy
                pos2d = p1 - p2
                speed = pos2d.length() / self.dt
                vc = math.degrees(math.atan2(pos2d.getY(), pos2d.getX()))
                if vc < 0.0:
                    vc += 360.0
                if abs(vc - self.velocityHeading) > 1:
                    self.db(f" Velocity vector changed: lstPos: ({p1.x:3.4f},{p1.y:3.4f}) now: ({p2.x:3.4f},{p2.y:3.4f})")
                self.velocityHeading = vc
                self.lstPos = self.actPos
                self.actPos = actPos
                vh = self.velocityHeading
                fc = self.facing
                if vh > 180.0: vh -= 360.0
                if fc > 180.0: fc -= 360.0
                #TODO: figure out speed direct wrt to tilt to be able to accelerate and decelerate correctly.
                if abs (vh - fc) >= 90.0: #pD.x < 0.0 or pD.y < 0: #abs(abs(self.velocityHeading - self.facing) - 180.0) < 2.0:
                    #going backgwards 
                    speed *= -1.0
                speedAvg = self.speed * self.lgShare + speed * self.smShare
                accel = (speedAvg - self.speed) / self.dt
                self.accel = self.accel * self.lgShare + accel * self.smShare
                self.speed = speedAvg
                self.lastUpdate = now

    def setSpeed(self, speed):
        self.db(f" ============================== requested velocity: {speed:3.4f}")
        if speed > self.MAX_SPEED: speed = self.MAX_SPEED
        if abs(speed) < 0.0001:
            self.trg = 0.0
            #self.sendEvent(self.STOP_EVT)
            self.db(f" ============================== STOP, zero: {self.trg:3.4f}")
        else:
            if True: #abs(self.trg - speed) > self.tol:
                self.trg = speed
                self.sendEvent(self.ACCEL_EVT)
                self.dump("SET SPD")
                self.velocityHeading = self.facing #reset the lock if a new speed target is set to start moving
                self.db(f" ============================== set velocity: {self.trg:3.4f}")

    def delta(self):
        return self.trg - self.speed

    def speedChanged(self, dir, update = True):
        drA = abs(self.prevSpeed - self.speed)
        if dir == "up":
            res = (self.speed > self.prevSpeed and drA > self.SPEED_CH_TOL)
        elif dir == "dn":
            res = (self.speed < self.prevSpeed and drA > self.SPEED_CH_TOL)
        else:
            res = (self.speed > self.prevSpeed and drA > self.SPEED_CH_TOL) or (self.speed < self.prevSpeed and drA > self.SPEED_CH_TOL)
        #self.db(f"Speed changed {dir}: {res},  {self.prevSpeed:5.5f} vs {self.speed:5.5f}")
        if update:
            self.prevSpeed = self.speed
        return res

    def setTilt(self, val):
        if abs(val) <= self.MAX_TILT:
            self.desTilt = val
            self.lastChange = time.time_ns()
            self.prevTilt = self.desTilt
            self.prevSpeed = self.speed
            self.db(f"Tilt Changed to: {val: 3.4f}")

    def pDiffN(self):
        pD = self.lstPos - self.actPos
        pD.normalize()
        return pD
    
    def getDot(self,h1,h2):
        vhRad = math.radians(h1)
        vhVec = Vec2(math.sin(vhRad), math.cos(vhRad))
        fcRad = math.radians(h2)
        fcVec = Vec2(math.sin(fcRad), math.cos(fcRad))
        dot = vhVec.dot(fcVec)
        return dot


    def isAlongPath(self):
        vh = self.velocityHeading
        fc = self.facing
        dot = self.getDot(vh,fc)
        stopped = abs(self.speed) <= self.tol
        along = (abs(dot) - 1.0)
        movingFwd = abs(abs(dot) - 1.0) < 0.01 and not stopped
        
        self.db(f" vh: {vh: 3.4f}, fc: {fc: 3.4f}, dot: {dot: 3.4f}, along: {along: 3.4f}, speed: {self.speed: 3.4f}, fwd: {movingFwd} or stopped {stopped}")
        return  movingFwd or stopped
    
    def isToTarget(self,trgHd):
        fc = self.facing
        dot = self.getDot(trgHd,fc)
        fwd = dot >= 0.0
        self.db(f" DEBUG1: DOT: {dot: 3.4f} to Target:{fwd},")
        return fwd


    def isStopped(self):
        return abs(self.speed) <= self.tol and abs(self.accel) < 0.0005 and abs(self.actTilt) < 0.05