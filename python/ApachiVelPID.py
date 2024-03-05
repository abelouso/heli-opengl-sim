#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec2, Vec3

import math
import queue
import inspect
import time
from BaseStateMachine import *

class ApachiVel(BaseStateMachine):

    MAINT_ST = 30
    CHANGE_ST = 31
    SIDE_ST = 32
    IDLE_ST = 33

    NULL_EVT = 30
    ACCEL_EVT = 31
    AT_SPEED_EVT = 32
    STOP_EVT = 33
    SIDE_EVT = 34
    FWD_EVT = 35
    IDLE_EVT = 36
    BUSY_EVT = 37

    MAX_TILT = 10.0
    MAX_ACCEL = 0.000006

    trg = 0.0
    speed = None
    tol = 0.00005
    
    desTilt = 0.0
    actTilt = 0.0
    
    actPos = None
    lstPos = None

    eventQ = queue.Queue()
    
    leave = None
    handle = None
    
    state = CHANGE_ST
    firstTick = True
    lastUpdate = time.time_ns()
    
    ##stable kick
    Kp = 7100.0
    Ki = 0.009
    Kd = 510000.0

    integLimit = 18.0
    #end stable kick
    
    error = None
    prevError = None
    integral = None
    derivitive = None
    lastStamp = lastUpdate
    lastChange = None
    dt = None
    facing = 0.0
    velocityHeading = 0.0

    NUM_SAMP = 150
    smShare = 1.0 / NUM_SAMP
    lgShare = 1.0 - smShare

    def dump(self, source):
        pDiff = self.pDiffN()
        cp = self.actPos
        lp = self.lstPos
        try:
            self.db(f"{source:5}, ApachVelPID T:{self.dt: 2.1f},veltrg:{self.trg: 3.6f},velspd:{self.speed: 3.6f}, "\
                    f"desT:{self.desTilt: 3.4f},velactT:{self.actTilt: 3.6f}, "\
                    f"err:{self.error: 3.9f},I:{self.integral: 3.9f},D:{self.derivitive: 3.9f}, "\
                    f"F:{self.facing: 3.4f},M:{self.velocityHeading: 3.4f} "\
                    f"lp:({lp.x: 3.4f},{lp.y: 3.4f},{lp.z: 3.4f}),cp:({cp.x: 3.4f},{cp.y: 3.4f},{cp.z: 3.4f})"\
                    f"dir:({pDiff.x: 3.4f},{pDiff.y: 3.4f},{pDiff.z: 3.4f})")
        except:
            pass

    def stopEvt(self):
        pass

    def maintHndl(self):
        pass

    def changeHndl(self):
        self.adjTilt()

    def sideHndl(self):
        pass

    def idleHndl(self):
        self.integral = 0.0
        self.setTilt(0.0)

    StateHandlers = {
        MAINT_ST: (     None,   maintHndl,   None),
        CHANGE_ST: (   None,   changeHndl,   None),
        SIDE_ST: (   None,   sideHndl,   None),
        IDLE_ST: ( None, idleHndl, None),
    }

    StateMachine = {
        CHANGE_ST: {
            IDLE_EVT: (IDLE_ST, None),
            ACCEL_EVT: (CHANGE_ST, None),
        },
        IDLE_ST: {
            ACCEL_EVT: (CHANGE_ST, None),
        },
    }

    def __init__(self):
        super().__init__("ApachiVel",0x8)
        self.state = self.CHANGE_ST
        self.velocityHeading = 0.0
        self.lstPos = self.actPos

    def tick(self, actPos4, tilt, dt, alt, facing):
        #self.updateTimeStamp()
        self.alt = alt
        actPos = Vec3(actPos4.getX(), actPos4.getY(), actPos4.getZ())
        self.actTilt = tilt
        self.prevFacing = self.facing
        self.facing = facing
        
        now = actPos4.getW() #time.time_ns()
        if self.lastChange is None:
            self.lastChange = now
            self.speed = 0.0
            return self.desTilt
        deltaT_us = now - self.lastChange
        deltaT_ms = 1000 * deltaT_us #0.000001 * deltaT_us
        if self.dt is not None:
            self.dt = self.lgShare * self.dt + self.smShare * deltaT_ms
        else:
            self.dt = deltaT_ms
        deltaT_ms = None
        
        if self.actPos is None:
            self.actPos = actPos
            speed = 0.0
            vc = facing
        else:
            p1 = actPos.xy
            p2 = self.actPos.xy
            pos2d = p1 - p2
            speed = pos2d.length() / self.dt
            vc = math.degrees(math.atan2(pos2d.getY(), pos2d.getX()))
            if vc < 0.0:
                vc += 360.0
            '''
            if abs(vc - self.velocityHeading) > 1:
                #self.db(f" Velocity vector changed: lstPos: ({p1.x:3.4f},{p1.y:3.4f}) now: ({p2.x:3.4f},{p2.y:3.4f})")
                pass
            '''
        if self.speed is None:
            self.speed = speed
        else:
            self.speed = speed #self.lgShare * self.speed + self.smShare * speed
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
            self.speed *= -1.0

        self.prevError = self.error
        self.error = self.getError()
        if self.prevError is not None:
            der = 100.0 * (self.error - self.prevError) / self.dt
            self.derivitive = der #self.lgShare * self.derivitive + self.smShare * der
        else:
            self.derivitive = 100.0 * self.error
        area = 10.0 * self.error * self.dt
        if self.integral is None:
            self.integral = area
        else:
            self.integral += area
        self.integral = self.clamp(self.integral,self.integLimit)
        if alt < 1.0: #abs(self.desTilt - self.actTilt) > 0.0001 or (alt < 1.0):
            self.dump("WAIT")
        else:
            self.dump("TICK")
            if self.handle is not None:
                self.handle(self)
        self.next()
        self.lastChange = now
        return self.desTilt

    
    def setSpeed(self, speed):
        self.db(f" ============================== requested velocity: {speed:3.4f}")
        #if speed > self.MAX_SPEED: speed = self.MAX_SPEED
        if abs(speed) < 0.0001:
            self.trg = 0.0
            #self.sendEvent(self.STOP_EVT)
            self.db(f" ============================== STOP, zero: {self.trg:3.4f}")
        else:
            if True: #abs(self.trg - speed) > self.tol:
                self.integral = 0.0
                self.trg = speed
                self.sendEvent(self.ACCEL_EVT)
                self.dump("SET SPD")
                self.velocityHeading = self.facing #reset the lock if a new speed target is set to start moving
                self.db(f" ============================== set velocity: {self.trg:3.4f}")

    def delta(self):
        if self.speed is not None:
            return self.trg - self.speed
        else:
            return self.trg
    

    def setTilt(self, val):
        if val >= self.MAX_TILT:
            val = self.MAX_TILT
        elif val <= -self.MAX_TILT:
            val = -self.MAX_TILT
        if abs(val) <= self.MAX_TILT:
            self.desTilt = val
            self.lastChange = time.time_ns()
            self.prevTilt = self.desTilt
            self.prevSpeed = self.speed
            #self.db(f"Tilt Changed to: {val: 3.4f}")

    def pDiffN(self):
        pD = self.lstPos - self.actPos
        pD.normalize()
        return pD

    def getError(self):
        return self.trg - self.speed
    
    def kickShare(self):
        error = self.error
        share = self.Kp * error + self.Ki * self.integral + self.Kd * self.derivitive
        return share

    def adjTilt(self):
        share = self.kickShare()
        #TODO limit tilt
        self.setTilt(share)

    def isStable(self):
        try:
            inTol = abs(self.delta()) <= self.tol
        #                               0.000000298
            stable = self.derivitive <= 0.0000006
        except:
            inTol = False
            stable = True
        return inTol and stable
    
    def isStopped(self):
        stab = self.isStable()
        return stab and abs(self.trg) < 0.0001
    
    def isAlongPath(self):
        vh = self.velocityHeading
        fc = self.facing
        dot = self.getDot(vh,fc)
        stopped = self.isStopped()
        along = (abs(dot) - 1.0)
        movingFwd = abs(abs(dot) - 1.0) < 0.01 and not stopped
        
        self.db(f" vh: {vh: 3.4f}, fc: {fc: 3.4f}, dot: {dot: 3.4f}, along: {along: 3.4f}, speed: {self.speed: 3.4f}, fwd: {movingFwd} or stopped {stopped}")
        return  movingFwd or stopped
    
    def isFwd(self):
        
        vh = self.velocityHeading
        fc = self.facing
        dot = self.getDot(vh,fc)
        mvFwd = abs(dot - 1.0) <= 0.01
        stopped = self.isStopped()
        return mvFwd or stopped

    def isToTarget(self,trgHd):
        fc = self.facing
        dot = self.getDot(trgHd,fc)
        fwd = dot >= 0.0
        self.db(f" DEBUG1: DOT: {dot: 3.4f} to Target:{fwd},")
        return fwd