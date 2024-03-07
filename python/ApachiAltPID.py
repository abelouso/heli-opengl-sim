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
    SHT_DWN_ST = 6

    NEW_ALT_EVT_EVT = 250
    AT_ALT_EVT = 251
    ROTOR_STARTED_EVT = 252
    STOP_EVT = 253

    eventQ = queue.Queue()
    leave = None
    handle = None

    trg = 0.0
    act = 0.0
    tol = 2.0

    MAX_RATE = 0.000003
    MAX_ACCEL = 0.00000001
    trgRate = MAX_RATE
    altRate = 0.0

    maxKick = 60.0
    desRotSpd = 0.0
    actMainSpd = 0.0
    
    dt = 0
    state = GND_ST
    firstTick = True
    
    lastUpdate = time.time_ns()

    MAX_ROT_SPD = 292.0
    TAKE_OFF_SPEED = 315.0 #313, half tank#
    TAKE_OFF_SPEED = 290.0 #313, 5% tank#


    MIN_ROT_SPD = 282.0 #2.0 * TAKE_OFF_SPEED - MAX_ROT_SPD

    TAKE_OFF_SPEED_0 = 223.0 #5%
    MAX_ROT_SPD_0 = TAKE_OFF_SPEED_0 + 16.0
    MIN_ROT_SPD_0 = TAKE_OFF_SPEED_0 - 16.0

    
    TAKE_OFF_SPEED_50 = 280.0 #50%
    MAX_ROT_SPD_50 = TAKE_OFF_SPEED_50 + 15.0
    MIN_ROT_SPD_50 = TAKE_OFF_SPEED_50 - 15.0
    
    TAKE_OFF_SPEED_100 = 343.3 #50%
    MAX_ROT_SPD_100 = TAKE_OFF_SPEED_100 + 26.0
    MIN_ROT_SPD_100 = TAKE_OFF_SPEED_100 - 26.0

    KCTR = (TAKE_OFF_SPEED_100 - TAKE_OFF_SPEED_0) / (1.0 - 0.05)
    BCTR = TAKE_OFF_SPEED_100 - KCTR * 1.0

    KLIM = (20.0 - 10.0) / (1.0 - 0.05)
    BLIM = 20.0 - KLIM * 1.0

    takeOffSpd = TAKE_OFF_SPEED_100
    maxRotSpd = MAX_ROT_SPD_100
    minRotSpd = MAX_ROT_SPD_100
    #relative kick -works on first landing
    '''
    Kp = 17.0
    Ki = 0.00044
    Kd = 160000.0
    integLimit = 110000.0
    '''
    #end relative kick

    #absolute
    Kp = 49.21
    Ki = 0.0008
    Kd = 250000.0
    lKp = 52.21
    lKi = 0.0008
    lKd = 2050000.0

    integLimit = 710000.0

    #original worked
    '''
    lKp = 12.21
    lKi = 0.00023
    lKd = 645000.0
    '''
    #end original


    #testing things
    Kp = 17.6
    Ki = 0.00047
    Kd = 156000.0

    lKp = 17.5
    lKi = 0.00044
    lKd = 187600.0
    integLimit = 110000.0
    #end low fuel


    isLanding = False
    areaKick = 10000.0

    error = None
    prevError = None
    integral = None
    derivitive = None
    lastStamp = lastUpdate
    lastChange = None
    startTime = None

    def dump(self,source):
        self.db(f"{source:10}, ApachiAltPID alttrg: {self.trg: 3.4f}, altact: {self.act: 3.4f}, "\
                f"alttrgrate: {self.trgRate: 3.9f}, altactrate: {self.altRate: 3.9f}, altaccel: {self.accel:3.9f},"\
                f"error: {self.error: 3.9f}, integral: {self.integral: 3.8f}, deriv: {self.derivitive: 3.8f},TOS:{self.takeOffSpd:>+4.1f}, "\
                f"act rot: {self.actMainSpd: 3.4f}, des rot: {self.desRotSpd: 3.4f},")
        pass


    def gndHndl(self):
        #self.setMainRotorSpeed(self.TAKE_OFF_SPEED)
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
    def shtHndl(self):
        self.setMainRotorSpeed(0.0)

    StateHandlers = {
        GND_ST:    (None, gndHndl, None),
        AT_ALT_ST: (None, atAltHndl, None),
        ALT_CHG_ST: (None, altChgHndl, None),
        SHT_DWN_ST: (None, shtHndl, None),
    }

    StateMachine = {
        GND_ST: {
            ROTOR_STARTED_EVT: (ALT_CHG_ST, None),
            NEW_ALT_EVT_EVT: (GND_ST, None),
        },
        AT_ALT_ST: {
            NEW_ALT_EVT_EVT: (ALT_CHG_ST, None),
            STOP_EVT: (SHT_DWN_ST, None)
        },
        ALT_CHG_ST: {
            AT_ALT_EVT: (AT_ALT_ST, None),
        },
        SHT_DWN_ST: {
            NEW_ALT_EVT_EVT: (GND_ST, None),
        },
    }

    def __init__(self):
        super().__init__(self.TAG, self.DBG_MASK)
        self.state = self.GND_ST
        self.sendEvent(self.NULL_EVT)
        self.startTime = time.time_ns()
    
    def tick(self, act, spd, dt,fp):
        #self.updateTimeStamp()
        self.fuel = 0.01 * fp
        self.takeOffSpd = self.KCTR * self.fuel + self.BCTR
        self.minRotSpd = self.takeOffSpd - (self.KLIM * self.fuel + self.BLIM)
        self.maxRotSpd = self.takeOffSpd + (self.KLIM * self.fuel + self.BLIM)
        now = dt
        if self.lastChange is None:
            self.lastChange = now
        else:
            deltaT_us = now - self.lastChange
            deltaT_ms = 1000.0 * deltaT_us
            self.dt = deltaT_ms
            deltaT_ms = None
            altRate = (act - self.act) / self.dt
            if self.altRate is not None:
                self.accel = (altRate - self.altRate) / self.dt
            self.altRate = altRate
            self.maxKick = 60.0 * 0.001 * self.dt
            self.act = act
            self.actMainSpd = spd
            self.prevError = self.error
            self.error = self.getError()
            if self.prevError is not None:
                self.derivitive = (self.error - self.prevError) / self.dt
            else:
                self.derivitive = 0.0
            area = self.areaKick * self.dt * self.error
            if self.integral is not None:
                self.integral += area
            else:
                self.integral = area
            self.integral = self.clamp(self.integral,self.integLimit)

            #adjust Kds as function of elapsed time
            '''
            elTime_s = 1.0e-9 * (time.time_ns() - self.startTime)
            tmRat = 0.033
            self.Kd +=  2.0
            self.Kp +=  0.001
            self.Ki +=  0.00000001

            self.lKd -= 1.2
            self.lKp += 0.0001
            self.lKi += 0.00000001
            '''

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
        prop = self.Kp * self.error
        inte = self.Ki * self.integral
        deri = self.Kd * self.derivitive
        self.db(f"DEBUG2: alt err: {prop: >+3.9f} int: {inte: >+3.9f} der: {deri: >+3.9f} kick: {share: >+3.9f} L:{self.isLanding},")
        return share
    
    def adjRotSpd(self):
        share = self.kickShare()
        #fixed base kick - works
        newSpd = self.takeOffSpd + share
        #end fixed base kick
        #absolute value
        '''
        ac = self.accel
        if abs(ac) > self.MAX_ACCEL:
            #take measure to slow down
            if ac > 0.0:
                wh = " kicked down"
                newSpd = self.desRotSpd - 0.01
            elif ac < 0.0:
                wh = " kicked up"
                newSpd = self.desRotSpd + 0.01
            else:
                wh = " set to current speed"
                newSpd = self.actMainSpd
            self.db(f" ___OVER MAX ACCEL__: {wh}")
        else:
            #set new desired speed
            newSpd = share
        '''
        #newSpd = share
        #end absolute value
        #relative kick
        #newSpd = self.desRotSpd + share
        #end relarive kick
        if newSpd > self.maxRotSpd: newSpd = self.maxRotSpd
        if newSpd < self.minRotSpd: newSpd = self.minRotSpd
        self.setMainRotorSpeed(newSpd)

    def isStable(self):
        stable = abs(self.getError()) <= self.tol and abs(self.derivitive) < 0.0001
        return stable