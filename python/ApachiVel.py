#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec4

import math
import queue
import inspect
import time
from BaseStateMachine import *

class ApachiVel(BaseStateMachine):

    MAINT_ST = 30
    CHANGE_ST = 31

    NULL_EVT = 30
    ACCEL_EVT = 31
    AT_SPEED_EVT = 32
    STOP_EVT = 33

    TILT_STEP = 0.03
    MAX_SPEED = 1.0
    MAX_TILT = 4.0
    SPEED_CH_TOL = 0.00002
    speed = 0.0
    prevSpeed = 0.0
    trg = 0.0
    actPos = Vec3(0,0,0)

    desTilt = 0.0
    actTilt = 0.0
    prevTilt = 0.0

    accel = 0.0

    tol = 0.02
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

    def dump(self, source):
        self.db(f"{source:10},T: {self.trg: 3.4f}, spd: {self.speed: 3.4f}, desT: {self.desTilt: 3.4f}, actT: {self.actTilt: 3.4f}, accel: {self.accel: 3.4f}, facing: {self.facing: 3.4f}, moving: {self.velocityHeading: 3.4f}")

    def stopEvt(self):
        self.setTilt(0.0)

    def maintHndl(self):
        
        dV = self.delta()
        self.db(f" delta V: {dV:3.4f}")
        if abs(dV) > self.tol:
            self.db(f" transition to ACCEL ST")
            self.sendEvent(self.ACCEL_EVT)

    def changeHndl(self):
        dV = self.delta()
        if abs(dV) < self.tol:
            #self.sendEvent(self.AT_SPEED_EVT)
            pass
        else:
            chUp = self.speedChanged("up",False)
            chDn = self.speedChanged("dn",True)
            if self.speed < self.trg - self.tol:
                #accelerating
                if self.speed < self.trg and not chUp:
                    self.setTilt(self.desTilt + self.TILT_STEP)
            elif self.speed > self.trg:
                #decelerating
                if self.speed > self.trg and not chDn:
                    self.setTilt(self.desTilt - self.TILT_STEP)

    
    StateHandlers = {
        MAINT_ST: (     None,   maintHndl,   None),
        CHANGE_ST: (   None,   changeHndl,   None),
    }

    StateMachine = {
        MAINT_ST: {
            ACCEL_EVT: (CHANGE_ST, None),
            STOP_EVT: (MAINT_ST, stopEvt),
            AT_SPEED_EVT: (MAINT_ST, None),
            NULL_EVT: (MAINT_ST, None),
        },
        CHANGE_ST: {
            ACCEL_EVT: (CHANGE_ST, None),
            STOP_EVT: (MAINT_ST, stopEvt),
            AT_SPEED_EVT: (MAINT_ST, None),
            NULL_EVT: (CHANGE_ST, None),
        },
    }

    def __init__(self):
        super().__init__("ApachiVel",0x8)
        self.state = self.MAINT_ST
        self.velocityHeading = 0.0

    def tick(self, actPos, tilt, dt, alt, facing):
        self.updateTimeStamp()
        self.alt = alt
        pos3d = Vec3(actPos.getX(), actPos.getY(), actPos.getZ())
        self.actTilt = tilt
        self.updateSpeed(pos3d)
        self.actPos = pos3d
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
        if self.alt > 0.2:
            p1 = actPos.xy
            p2 = self.actPos.xy
            pos2d = p1 - p2
            speed = pos2d.length() / self.dt
            self.velocityHeading = math.degrees(math.atan2(pos2d.getY(), pos2d.getX()))
            if self.velocityHeading < 0.0:
                self.velocityHeading += 360.0
            if abs(abs(self.velocityHeading - self.facing) - 180.0) < 2.0:
                #going backgwards 
                speed *= -1.0
            elif abs(self.velocityHeading - self.facing) > 3.0 and abs(self.speed) > self.tol:
                #drifting, stop
                #self.setTilt(0.0)
                #self.sendEvent(self.STOP_EVT)
                pass
            speedAvg = self.speed * self.lgShare + speed * self.smShare
            accel = (speedAvg - self.speed) / self.dt
            self.accel = self.accel * self.lgShare + accel * self.smShare
            self.speed = speedAvg

    def setSpeed(self, speed):
        self.db(f" ============================== requested velocity: {speed:3.4f}")
        if speed > self.MAX_SPEED: speed = self.MAX_SPEED
        if abs(speed) < 0.0001:
            self.trg = 0.0
            self.sendEvent(self.STOP_EVT)
            self.db(f" ============================== STOP, zero: {self.trg:3.4f}")
        else:
            if abs(self.trg - speed) > self.tol:
                self.trg = speed
                self.sendEvent(self.ACCEL_EVT)
                self.dump("SET SPD")
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
        if abs(val) < self.MAX_TILT:
            self.desTilt = val
            self.lastChange = time.time_ns()
            self.prevTilt = self.desTilt
            self.prevSpeed = self.speed
            self.db(f"Tilt Changed to: {val: 3.4f}")