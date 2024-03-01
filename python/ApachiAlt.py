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
    UP_ACCEL_ST = 2
    UP_LIN_ST = 3
    UP_DECEL_ST = 4
    AT_ALT_ST = 5
    DOWN_ACCEL_ST = 6
    DOWN_LIN_ST = 7
    DOWN_DECEL_ST = 8
    TAKE_OFF_ST = 9

    DONE_EVT = 200
    NULL_EVT = 201
    ACCND_EVT = 203
    DECND_EVT = 204
    DECEL_EVT = 205

    MAX_ALT_RATE = 1.0
    ROT_SPD_DELTA_SLOW = 1.4
    ROT_SPD_DELTA_FAST = 3.5
    ROT_SLOT_FAST_BREAK = 65
    RATE_TOL = 0.001
    WAIT_FOR_CHANGE_NS = 200.0e3 #200 ms
    rotSpdDelta = ROT_SPD_DELTA_FAST

    accelAlt = 0
    linAlt = 0

    deltaRot = 0

    altCnt = 20
    smAltShare = 1.0 / float(altCnt)
    lgAltShare = 1.0 - smAltShare

    changeStamp = time.time_ns()
    lastStamp = time.time_ns()
    
    leave = None
    handle = None
    
    dt = 0
    state = GND_ST
    firstTick = True

    def dump(self,source):
        self.db(f"{source:10}, alttrg: {self.trg: 3.4f}, altact: {self.act: 3.4f}, "\
                f"altrate: {self.altRate: 3.4f}, altaccel: {self.altAccel: 3.8f}, "\
                f"act rot: {self.actMainSpd: 3.4f}, des rot: {self.desRotSpd: 3.4f},")
        pass


    def gndHndl(self):
        da = self.getDeltaAlt()
        if da > 0.0:
            self.sendEvent(self.ACCND_EVT)

    def inGndHndl(self):
        pass

    def outGndHndl(self):
        pass

    def accndEvt(self):
        pass

    def nullEvt(self):
        pass


    def inAccelHndl(self):
        da = self.getDeltaAlt()
        if da > 0:
            accelInt = math.fabs(0.5 * da)
            self.accelAlt = self.act + accelInt
            self.linAlt = self.accelAlt + accelInt
        else:
            accelInt = math.fabs(0.45 * da)
            self.accelAlt = self.act - accelInt
            self.linAlt = self.accelAlt - accelInt
        

    def upAccelHndl(self):
        da = self.getDeltaAlt()
        
        #if self.act > self.accelAlt:
        done = abs(da) <= 32.0
        self.db(f"DEBUG2: UPACCEL: da {abs(da):3.4f} <= 32.0: = {done},")
        if done:
            self.db(f"== TRANSITION TO LINEAR == ")
            self.sendEvent(self.DECEL_EVT)
        else:
            chg = self.rateChanged("up")
            if not chg and self.altRate < 0.5 * self.MAX_ALT_RATE:
                self.setMainRotorSpeed(self.desRotSpd + self.rotSpdDelta)
            elif chg and self.altRate > 0.9 * self.MAX_ALT_RATE:
                self.setMainRotorSpeed(self.desRotSpd - self.rotSpdDelta)
            else:
                self.deltaRot = self.desRotSpd - self.takeOfRotorSpeed


    def dnAccelHndl(self):
        da = self.getDeltaAlt()
        #if self.act < self.accelAlt:
        self.db(f"DEBUG2: DOWN ACC: da {abs(da):3.4f} <= 42.0,")
        if abs(da) <= 42.0:
            self.db(f" --- TRANSITION TO DOWN DECEL ---")
            self.sendEvent(self.DECEL_EVT)
        else:
            chg = self.rateChanged("dn")
            if not chg and self.altRate > -self.MAX_ALT_RATE:
                self.setMainRotorSpeed(self.desRotSpd - self.rotSpdDelta)
            elif chg and self.altRate < -self.MAX_ALT_RATE:
                self.setMainRotorSpeed(self.desRotSpd + self.rotSpdDelta)
              
    def inUpDecelHndl(self):
        self.db(f"Killing acceleration by {self.deltaRot:,}")
        self.setMainRotorSpeed(self.desRotSpd - self.deltaRot)

    def upDecelHndl(self):
        da = self.getDeltaAlt()
        chgDn = self.rateChanged("dn",False)
        chgUp = self.rateChanged("up")
        if math.fabs(da) < self.tol and math.fabs(self.altRate) < 0.1 and not chgDn and not chgUp:
            self.db(f"== TRANSITION TO AT ALT == ")
            self.sendEvent(self.DONE_EVT)
        else:
            if (not chgDn and self.altRate > 0.1) or (chgUp and self.altRate > 0.05): #need to be change rate to zero, not changing up if the rate is positive
                self.setMainRotorSpeed(self.desRotSpd - self.rotSpdDelta)
            elif chgDn and self.altRate < 0.0:
                self.setMainRotorSpeed(self.desRotSpd + self.rotSpdDelta)
            if da > self.tol and not chgUp and self.altRate < 0.1:
                self.db(f"Slowed down too soon, kick it up")
                self.setMainRotorSpeed(self.desRotSpd + self.rotSpdDelta)
            if math.fabs(da) > (2.0 * self.tol) and da < 0.0:
                self.db("=== Way way past, go down ===")
                self.sendEvent(self.DECND_EVT)

    def dnDecelHndl(self):
        da = self.getDeltaAlt()
        chgDn = self.rateChanged("dn",False)
        chgUp = self.rateChanged("up")
        if math.fabs(da) < self.tol and math.fabs(self.altRate) < 0.1 and not chgDn and not chgUp:
            self.db(f"== TRANSITION TO AT ALT == ")
            self.sendEvent(self.DONE_EVT)
        else:
            if (not chgUp and self.altRate < 0.0) or (chgDn and self.altRate < -0.1):  #have to change rate up if not change or cannot change down with the negative rate
                self.setMainRotorSpeed(self.desRotSpd + self.rotSpdDelta)
            elif chgUp and self.altRate > 0.0:
                self.setMainRotorSpeed(self.desRotSpd - self.rotSpdDelta)
            if math.fabs(da) > self.tol and da < 0 and self.altRate > -0.1 and not chgDn:
                self.db(f"Slow down the decent too soon, kick it down")
                self.setMainRotorSpeed(self.desRotSpd - self.rotSpdDelta)

            if math.fabs(da) > (2.0 * self.tol) and da > 0.0:
                self.db("=== Way way past, go up ===")
                self.sendEvent(self.ACCND_EVT)
                
    
    def takeOffHndl(self):
        if self.act > 0.0:
            self.db(" == TAKEN OFF == ")
            self.sendEvent(self.ACCND_EVT)
        else:
            now = time.time_ns()
            if now - self.changeStamp > self.WAIT_FOR_CHANGE_NS:
                self.setMainRotorSpeed(self.desRotSpd + self.rotSpdDelta)

    def leaveTkOffHndl(self):
        #stabilize the flight
        if self.trg >= self.ROT_SLOT_FAST_BREAK:
            self.db("==================== Stabilizing flight")
            self.setMainRotorSpeed(400) #1.1 * self.desRotSpd)
            self.rotSpdDelta = self.ROT_SPD_DELTA_FAST
        else:
            self.rotSpdDelta = self.ROT_SPD_DELTA_SLOW
        #self.correctRate = False
        pass

    
    def atAltHndl(self):
        chg = self.rateChanged("up",False)
        if not chg and self.altRate < -0.0025:
            self.setMainRotorSpeed(self.desRotSpd + 0.44 * self.rotSpdDelta)
        elif chg and self.altRate > -0.0075:
            self.setMainRotorSpeed(self.desRotSpd - 0.67 * self.rotSpdDelta)

    def atAltHndlHmm(self):
        da = self.getDeltaAlt()
        chgDn = self.rateChanged("dn",False)
        chgUp = self.rateChanged("up")
        if (not chgDn and self.altRate > 0.1) or (chgUp and self.altRate > 0.05): #need to be change rate to zero, not changing up if the rate is positive
            self.setMainRotorSpeed(self.desRotSpd - 0.5 * self.rotSpdDelta)
        elif chgDn and self.altRate < 0.0:
            self.setMainRotorSpeed(self.desRotSpd + 0.5 * self.rotSpdDelta)
        if da > self.tol and not chgUp and self.altRate < 0.1:
            self.db(f"Slowed down too soon, kick it up")
            self.setMainRotorSpeed(self.desRotSpd + 0.5 * self.rotSpdDelta)
        '''
        if (not chgUp and self.altRate < 0.0) or (chgDn and self.altRate < -0.1):  #have to change rate up if not change or cannot change down with the negative rate
                self.setMainRotorSpeed(self.desRotSpd + self.rotSpdDelta)
        elif chgUp and self.altRate > 0.0:
            self.setMainRotorSpeed(self.desRotSpd - self.rotSpdDelta)
        if math.fabs(da) > self.tol and da < 0 and self.altRate > -0.1 and not chgDn:
            self.db(f"Slow down the decent too soon, kick it down")
            self.setMainRotorSpeed(self.desRotSpd - self.rotSpdDelta)
        '''


    def inAtAltHndl(self):
        self.rotSpdDelta = self.ROT_SPD_DELTA_FAST
    
    StateHandlers = {
        GND_ST: (inGndHndl, gndHndl, outGndHndl),
        UP_ACCEL_ST: (inAccelHndl, upAccelHndl, None),
        UP_DECEL_ST: (inUpDecelHndl, upDecelHndl, None),
        AT_ALT_ST: (inAtAltHndl, atAltHndl, None),
        DOWN_ACCEL_ST: (inAccelHndl, dnAccelHndl, None),
        DOWN_LIN_ST: (None, None, None),
        DOWN_DECEL_ST: (None, dnDecelHndl, None),
        TAKE_OFF_ST: (None, takeOffHndl, leaveTkOffHndl),
    }
    
    StateMachine = {
        GND_ST: { NULL_EVT: (GND_ST, nullEvt),
                  DONE_EVT: (AT_ALT_ST, None),
                  ACCND_EVT: (TAKE_OFF_ST, None),
                  DECND_EVT: (GND_ST, None),
        },
        TAKE_OFF_ST: { NULL_EVT: (TAKE_OFF_ST, nullEvt),
                  DONE_EVT: (TAKE_OFF_ST, None),
                  ACCND_EVT: (UP_ACCEL_ST, None),
                  DECND_EVT: (TAKE_OFF_ST, None),
        },
        UP_ACCEL_ST: { NULL_EVT: (UP_ACCEL_ST, nullEvt),
                  DONE_EVT: (AT_ALT_ST, None),
                  DECEL_EVT: (UP_DECEL_ST, None),
                  DECND_EVT: (DOWN_ACCEL_ST, None),
        },
        UP_DECEL_ST: { NULL_EVT: (UP_DECEL_ST, nullEvt),
                  DONE_EVT: (AT_ALT_ST, None),
                  ACCND_EVT: (UP_ACCEL_ST, accndEvt),
                  DECND_EVT: (DOWN_ACCEL_ST, None),
        },
        AT_ALT_ST: { NULL_EVT: (AT_ALT_ST, nullEvt),
                  DONE_EVT: (AT_ALT_ST, None),
                  ACCND_EVT: (UP_ACCEL_ST, None),
                  DECND_EVT: (DOWN_ACCEL_ST, None),
        },
        DOWN_ACCEL_ST: { NULL_EVT: (DOWN_ACCEL_ST, nullEvt),
                  DONE_EVT: (AT_ALT_ST, None),
                  ACCND_EVT: (UP_ACCEL_ST, accndEvt),
                  DECEL_EVT: (DOWN_DECEL_ST, None),
        },
        DOWN_DECEL_ST: { NULL_EVT: (DOWN_DECEL_ST, nullEvt),
                  DONE_EVT: (AT_ALT_ST, None),
                  ACCND_EVT: (UP_ACCEL_ST, accndEvt),
                  DECND_EVT: (DOWN_ACCEL_ST, None),
        },
    }

    def __init__(self):
        super().__init__(self.TAG, self.DBG_MASK)
        self.state = self.GND_ST
        self.trg = 0
        self.act = 0
        self.diff = 0.25
        self.tol = 0.5
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
        self.setMainRotorSpeed(0)
        self.prevAltRate = -1 # artificial rate change to start correcting

    def tick(self, act, spd, dt):
        now = time.time_ns()
        dt = (now - self.lastStamp) * 0.00000001 #ns
        self.dt = dt
        if dt >= 0.3:
            ##TODO: provide service for thisin heli main
            self.actMainSpd = spd
            altRate = (act - self.act) / self.dt
            #if math.fabs(altRate - self.altRate) > 0.5:
            #    altRate = self.altRate
            
            accel = (altRate - self.altRate) / self.dt
            self.altAccel = self.altAccel * self.lgAltShare + self.smAltShare * accel
            #sliding average
            self.altRate = self.altRate * self.lgAltShare + self.smAltShare * altRate
            self.act = act
            self.dump("TICK")
            #self.db(f"trg: {self.trg:5.2f}, act: {self.act:5.2f}, exp rt: {self.desRotSpd:5.2f}, act rt: {self.actMainSpd:5.2f}, rate: {self.altRate:5.5f}/{altRate:5.5f}, rt accel: {self.altAccel:5.2f}, dt: {dt:5.5f}, step: {self.rotSpdDelta:5.2f}")
            if self.takeOfRotorSpeed is None and self.act > 0.0:
                self.takeOfRotorSpeed = self.desRotSpd
            if math.fabs(self.desRotSpd - self.actMainSpd) > 0.001:
                self.db(f"Rotor spinning up/down: req: {self.desRotSpd:5.2f}, actual {self.actMainSpd:5.2f}, rate: {self.altRate:5.2f}, alt: {self.act:5.2f}")
            else:
                if self.handle is not None:
                    self.handle(self)
            self.next()
            self.lastStamp = now
        return self.desRotSpd
    
    def getDeltaAlt(self):
        da = self.trg - self.act
        return da
    
    def calcDeltaSpd(self,da):
        dSpd = self.spCoeff * da * self.diff * (math.exp(2) - 1.0)
        self.db(f"calcDeltaSpd: Correction: rate: {self.altRate}, act {self.act}, trg: {self.trg}, spd: {self.desRotSpd}, dAlt {da}, dSpd: {dSpd}, new speed {self.desRotSpd + dSpd}")
        return dSpd

    def calcKick(self, curRate, desRate, curSpd):
        pass

    def setTarget(self,trg):
        self.trg = trg
        da = self.getDeltaAlt()
        if math.fabs(da) > self.tol:
            if self.trg > self.act:
                self.sendEvent(self.ACCND_EVT)
            elif self.trg < self.act:
                    self.sendEvent(self.DECND_EVT)
            self.rotSpdDelta = self.ROT_SPD_DELTA_SLOW
            if (math.fabs(da) >= self.ROT_SLOT_FAST_BREAK) or da > 0.0:
                self.rotSpdDelta = self.ROT_SPD_DELTA_FAST
                #self.setMainRotorSpeed(390)
            else:
                self.rotSpdDelta = self.ROT_SPD_DELTA_SLOW
        self.db(f"DEBUG1: rotDelta: {self.rotSpdDelta: 3.4f},")

    def rotorSpeed(self):
        return self.desRotSpd
    
    def setMainRotorSpeed(self,spd):
        if spd >= 0.0 and spd <= 400.0:
            self.desRotSpd = spd
        self.prevAltRate = self.altRate
        self.changeStamp = time.time_ns()
        self.db(f"Rotor speed changed to {self.desRotSpd:5.2f}, alt: {self.act:5.2f}")

    def rateChanged(m,dir, update = True):
        drA = math.fabs(m.prevAltRate - m.altRate)
        if dir == "up":
            res = (m.altRate > m.prevAltRate and drA > m.RATE_TOL)
        elif dir == "dn":
            res = (m.altRate < m.prevAltRate and drA > m.RATE_TOL)
        else:
            res = (m.altRate > m.prevAltRate and drA > m.RATE_TOL) or (m.altRate < m.prevAltRate and drA > m.RATE_TOL)
        m.db(f"Rate changed {dir}: {res},  {m.prevAltRate:5.5f} vs {m.altRate:5.5f}")
        if update: m.prevAltRate = m.altRate
        return res
    
    def rateStable(m):
        drA = math.fabs(m.prevAltRate - m.altRate)
        return drA <= m.RATE_TOL
    
    def getMaxRate(self):
        da = self.getDeltaAlt()
        sign = 1.0
        if da < 0.0:
            sign = -1.0
        maxRate = sign * self.MAX_ALT_RATE
        return maxRate


if __name__ == "__main__":
    alt = ApachiAlt()
    alt.sendEvent(alt.NULL_EVT)
    alt.setTarget(100)
    alt.setMainRotorSpeed(100)
    alt.tick(100,100,0.1)
    alt.sendEvent(alt.ACCND_EVT)
    alt.tick(100,100,0.1)