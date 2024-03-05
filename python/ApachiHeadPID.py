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
    TURN_ST = 21

    NEW_HEAD_EVT = 25
    DONE_EVT = 26

    STABLE_SPEED = 100.0
    desRotSpd = STABLE_SPEED
    actRotSpd = 0.0
    tol = 0.1 #degrees
    alt = 0.0

    trg = 0.0
    act = 0.0

    eventQ = queue.Queue()
    
    leave = None
    handle = None
    
    state = AT_HEAD_ST
    firstTick = True
    lastUpdate = time.time_ns()

    ##Relative kick - works
    '''
    Kp = 0.002
    Ki = 0.0000000001
    Kd = 4.3
    integLimit = 10000.0
    '''
    #end relative kick
    
    ##stable kick
    Kp = 0.2
    Ki = 0.000000001
    Kd = 2.0
    integLimit = 10000.0
    #end stable kick

    error = 0.0
    prevError = 0.0
    integral = 0.0
    derivitive = 0.0
    lastStamp = lastUpdate
    lastChange = lastStamp

    def dump(self, source):
        dH = self.getError()
        self.db(f"{source:10} ApachiHeadPID trg: {self.trg: 3.4f}, act: {self.act: 3.4f}, dA: {dH: 3.4f}, desRS: {self.desRotSpd: 3.4f}, " \
                f"actRotSpd: {self.actRotSpd: 3.4}, int: {self.integral: 3.9f}, der: {self.derivitive: 3.9f}, dt: {self.dt: 3.4f}, elapsed: {self.alt: 3.4f},")

    def atHeadHndl(self):
        self.setRotorSpeed(self.STABLE_SPEED)

    def turnHndl(self):
        self.adjRotSpd()
        if self.isStable():
            self.sendEvent(self.DONE_EVT)
            pass

    
    StateHandlers = {
        AT_HEAD_ST: (None, atHeadHndl, None),
        TURN_ST: (None, turnHndl, None),
    }

    
    StateMachine = {
        AT_HEAD_ST: {
            NEW_HEAD_EVT: (TURN_ST, None),
        },
        TURN_ST: {
            DONE_EVT: (AT_HEAD_ST, None),
        },
    }

    def __init__(self):
        super().__init__("ApachiHead", 0x4)
        self.state = self.AT_HEAD_ST

    
    def tick(self, act, spd, dt, alt):
        self.updateTimeStamp()
        now = time.time_ns()
        deltaT_us = now - self.lastChange
        deltaT_ms = 0.000001 * deltaT_us
        self.dt = deltaT_ms
        self.actRotSpd = spd
        self.act = act
        self.alt = alt
        self.prevError = self.error
        self.error = self.getError()
        self.derivitive = (self.error - self.prevError) / deltaT_ms
        self.integral += deltaT_ms * (self.error)
        self.integral = self.clamp(self.integral,self.integLimit)

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

    def setHeading(self, heading):
        self.db(f" ============================================= Requested heading: {heading: 3.4f}")
        if heading < 0.0:
            heading = 360.0 + heading
        if True: #abs(heading - self.act) > self.tol:
            self.trg = heading
            self.sendEvent(self.NEW_HEAD_EVT)
            self.dump("SET HDG")
        self.db(f" ============================================= Set heading: {self.trg: 3.4f}")

    def deltaHead(self):
        return self.trg - self.act

    def setRotorSpeed(self, spd):
        self.desRotSpd = spd

    def isStable(self):
        stable = abs(self.getError()) <= self.tol and abs(self.derivitive) < 0.00001
        return stable
    
    def getError(self):
        trg180 = self.trg - 360.0 if self.trg > 180.0 else self.trg
        act180 = self.act - 360.0 if self.act > 180.0 else self.act
        err = trg180 - act180
        if err >= 180.0: err -= 360.0
        return err


    def kickShare(self):
        error = self.error
        share = self.Kp * error + self.Ki * self.integral + self.Kd * self.derivitive
        ###self.db(f"DEBUG1: err: {error: 3.9f} int: {self.integral: 3.9f} der: {self.derivitive: 3.9f} kick: {share: 3.9f},")
        return share

    def adjRotSpd(self):
        share = self.kickShare()
        #reltive kick - works
        newSpd = self.desRotSpd + share
        #end relative kick
        #stable kick
        newSpd = self.STABLE_SPEED + share
        #end stable kick
        if newSpd > 119.9: newSpd = 119.9
        if newSpd < 80.1: nesSpd = 80.1
        self.setRotorSpeed(newSpd)