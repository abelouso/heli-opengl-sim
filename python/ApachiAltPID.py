#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec4

import math
import queue
import inspect
import time

from BaseStateMachine import *


class ApachiAlt(BaseStateMachine):
    TAG = "ApachiAlt"
    DBG_MASK = 0x0002
    GND_ST = 1
    AT_ALT_ST = 5
    TAKE_OFF_ST = 9
    ALT_CHG_ST = 2

    NEW_ALT_EVT_EVT = 250
    AT_ALT_EVT = 251
    ROTOR_STARTED_EVT = 252


    eventQ = queue.Queue()
    leave = None
    handle = None

    trg = 0.0
    act = 0.0
    tol = 2.0

    MAX_RATE = 0.000003
    trgRate = MAX_RATE
    altRate = 0.0

    maxKick = 60.0
    desRotSpd = 0.0
    actMainSpd = 0.0
    
    dt = 0
    state = GND_ST
    firstTick = True
    
    lastUpdate = time.time_ns()

    MAX_ROT_SPD = 399.0
    TAKE_OFF_SPEED = 347.0
    MIN_ROT_SPD = 200.0 #2.0 * TAKE_OFF_SPEED - MAX_ROT_SPD
    
    #relative kick -works on first landing
    '''
    Kp = 17.0
    Ki = 0.00044
    Kd = 160000.0
    integLimit = 110000.0
    '''
    #end relative kick

    Kp = 13.21
    Ki = 0.00023
    Kd = 29000.0

    lKp = 12.21
    lKi = 0.00023
    lKd = 645000.0

    integLimit = 11000000.0

    isLanding = False

    error = 0.0
    prevError = 0.0
    integral = 0.0
    derivitive = 0.0
    lastStamp = lastUpdate
    lastChange = lastStamp

    def dump(self,source):
        self.db(f"{source:10}, ApachiAltPID alttrg: {self.trg: 3.4f}, altact: {self.act: 3.4f}, "\
                f"alttrgrate: {self.trgRate: 3.9f}, altactrate: {self.altRate: 3.9f}, mxki: {self.maxKick:3.4f},"\
                f"error: {self.error: 3.9f}, integral: {self.integral: 3.8f}, deriv: {self.derivitive: 3.8f},"\
                f"act rot: {self.actMainSpd: 3.4f}, des rot: {self.desRotSpd: 3.4f},")
        pass


    def gndHndl(self):
        self.setMainRotorSpeed(self.TAKE_OFF_SPEED)
        self.sendEvent(self.ROTOR_STARTED_EVT)

    def atAltHndl(self):
        self.adjRotSpd()

    def altChgHndl(self):
        dA = self.getDeltaAlt()
        '''
        if abs(dA) < 4.0:
            self.trgRate = 0.0
        '''
        self.adjRotSpd()
        if self.isStable():
            self.sendEvent(self.AT_ALT_EVT)
            pass

    StateHandlers = {
        GND_ST:    (None, gndHndl, None),
        AT_ALT_ST: (None, atAltHndl, None),
        ALT_CHG_ST: (None, altChgHndl, None),
    }

    StateMachine = {
        GND_ST: {
            ROTOR_STARTED_EVT: (ALT_CHG_ST, None),
            NEW_ALT_EVT_EVT: (GND_ST, None),
        },
        AT_ALT_ST: {
            NEW_ALT_EVT_EVT: (ALT_CHG_ST, None),
        },
        ALT_CHG_ST: {
            AT_ALT_EVT: (AT_ALT_ST, None),
        },
    }

    def __init__(self):
        super().__init__(self.TAG, self.DBG_MASK)
        self.state = self.GND_ST
        self.sendEvent(self.NULL_EVT)
    
    def tick(self, act, spd, dt):
        self.updateTimeStamp()
        now = time.time_ns()
        deltaT_us = now - self.lastChange
        deltaT_ms = 0.000001 * deltaT_us
        self.dt = deltaT_ms
        self.altRate = (act - self.act) / deltaT_ms
        self.maxKick = 60.0 * 0.001 * deltaT_ms
        self.act = act
        self.actMainSpd = spd
        self.prevError = self.error
        self.error = self.getError()
        self.derivitive = (self.error - self.prevError) / deltaT_ms
        self.integral += 2.0 * deltaT_ms * (self.error)
        self.integral = self.clamp(self.integral,self.integLimit)
        if False: #math.fabs(self.desRotSpd - self.actMainSpd) > 0.001:
            self.dump("WAIT")
        else:
            if self.handle is not None:
                self.handle(self)
                self.dump("TICK")
        self.next()
        self.lastChange = now
        return self.desRotSpd
    
    def getDeltaAlt(self):
        da = self.trg - self.act
        return da
    
    def getError(self):
        return self.getDeltaAlt()
        #error = self.trgRate - self.altRate
        #return error
    
    def setTarget(self,trg):
        self.trg = trg
        self.isLanding = True if abs(trg < self.act) else False
        self.trgRate = self.MAX_RATE
        self.integral = 0.0
        self.sendEvent(self.NEW_ALT_EVT_EVT)

    def setMainRotorSpeed(self,spd):
        '''
        if spd >= 0.0 and spd <= 400.0:
            self.desRotSpd = spd
        '''
        self.desRotSpd = spd
        self.changeStamp = time.time_ns()
        self.db(f"Rotor speed changed to {self.desRotSpd:5.2f}, alt: {self.act:5.2f}")

    def kickShare(self):
        error = self.error
        if self.isLanding:
            share = self.lKp * error + self.lKi * self.integral + self.lKd * self.derivitive
        else:
            share = self.Kp * error + self.Ki * self.integral + self.Kd * self.derivitive
        '''
        if share >= 0.0:
            if share > self.maxKick: share = self.maxKick
        else:
            if share < -self.maxKick: share = -self.maxKick
        '''
        self.db(f"DEBUG2: alt err: {error: 3.9f} int: {self.integral: 3.9f} der: {self.derivitive: 3.9f} kick: {share: 3.9f} L:{self.isLanding},")
        return share
    
    def adjRotSpd(self):
        share = self.kickShare()
        #relative kick - works
        newSpd = self.TAKE_OFF_SPEED + share
        #end relative kick
        #absolute value
        newSpd = share
        #end absolute value
        if newSpd > self.MAX_ROT_SPD: newSpd = self.MAX_ROT_SPD
        if newSpd < self.MIN_ROT_SPD: newSpd = self.MIN_ROT_SPD
        self.setMainRotorSpeed(newSpd)

    def isStable(self):
        stable = abs(self.getError()) <= self.tol and abs(self.derivitive) < 0.0001
        return stable