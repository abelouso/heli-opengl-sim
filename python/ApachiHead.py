#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec4

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
    MAX_ROT_RATE = 2.0
    SPD_DELTA = 1.0
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

    tol = 0.3 #degrees
    alt = 0.0

    eventQ = queue.Queue()
    
    leave = None
    handle = None
    
    dt = 0
    lastStamp = time.time_ns()
    lastChange = lastStamp
    state = AT_HEAD_ST
    firstTick = True

    def dump(self, source):
        self.db(f"{source:10} ,T: {self.trg: 3.4f}, act: {self.act: 3.4f}, desRS: {self.desRotSpd: 3.4f}, actRotSpd: {self.actRotSpd: 3.4}, rotRate: {self.rotRate: 3.4f}, rotAccel: {self.rotAccel: 3.4f}")

    def newHeadEvt(self):
        # figure out positive or negative kick in the turn
        dh = self.deltaHead()
        dha = abs(dh)
        if dha > self.tol:
            #find the shortest turn
            if dha < 180:
                if self.trg > self.act:
                    self.setRotorSpeed(self.desRotSpd + self.SPD_DELTA)
                    self.rateSign = 1.0
                else:
                    self.setRotorSpeed(self.desRotSpd - self.SPD_DELTA)
                    self.rateSign = -1.0
            else:
                if self.trg > self.act:
                    self.setRotorSpeed(self.desRotSpd - self.SPD_DELTA)
                    self.rateSign = -1.0
                else:
                    self.setRotorSpeed(self.desRotSpd + self.SPD_DELTA)
                    self.rateSign = 1.0

    def kickHndl(self):
        dh = self.deltaHead()
        if abs(dh) < self.tol:
            self.db(f" Going to LOCK: {self.trg: 3.4f}, act: {self.act: 3.4f}, dh: {dh: 3.4f}")
            self.sendEvent(self.STOP_EVT)
        #elif abs(dh) < 1:
        #    self.sendEvent(self.DONE_EVT)
        else:
            chUp = self.rateChanged("up")
            adjRt = self.rateSign * self.rotRate
            adjRtMax = self.rateSign * self.MAX_ROT_RATE
            adj = self.rateSign * self.SPD_DELTA
            self.db(f"In kick hdn: {adjRt: 3.4f}, MAX: {adjRtMax: 3.4f}, step: {adj: 3.4f}")
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
        dh = self.deltaHead()
        if abs(dh) < self.tol:
            self.sendEvent(self.LOCK_EVT)
        else:
            chDn = self.rateChanged("dn")
            if not chDn and self.rotRate > 0.0:
                self.setRotorSpeed(self.desRotSpd - self.SPD_DELTA)
            elif chDn and self.rotRate < 0.0:
                self.setRotorSpeed(self.desRotSpd + self.SPD_DELTA)
    def atHeadHndl(self):
        dh = self.deltaHead()
        self.db(f" dh:  {dh:3.4f}")
        if abs(dh) > (1.5 * self.tol):
            #correct if too far out
            self.newHeadEvt()
            self.sendEvent(self.DONE_EVT)
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
        self.act = act
        if abs(self.desRotSpd - self.actRotSpd) > 0.001 or not self.alt > 1.0:
            self.dump("WAIT")
        else:
            self.dump("TICK")
            if self.handle is not None:
                self.handle(self)
        self.next()
        self.lastChange = time.time_ns()
        return self.desRotSpd

    def updateActRotRate(self,act):
        rotRate = (act - self.act) / self.dt
        if abs(rotRate - self.rotRate) > 4: #to accoutn large swings in rotation rate changes
            rotRate = self.rotRate
        rotRatAvg = self.rotRate * self.lgShare + rotRate * self.smShare
        #self.db(f" act: {act:3.4f}, prev act: {self.act}, dt: {self.dt}, instRot: {rotRate:3.4f}, avg: {rotRatAvg:3.4f}, lgShare: {self.lgShare:3.4f}, smShare: {self.smShare:3.4f}")
        self.rotAccel = (rotRatAvg - self.rotRate) / self.dt
        self.rotRate = rotRatAvg

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