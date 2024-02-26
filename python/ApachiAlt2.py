import queue
import time
import math

from BaseStateMachine import *


class ApachiAlt(BaseStateMachine):

    TAG = "ApachiAlt"
    DBG_MASK = 0x2
    NULL_EVT = 0
    GND_ST = 1
    ALT_CHG_ST = 2
    AT_ALT_ST = 3

    TAKE_OFF_EVT = 0
    AT_ALT_EVT = 1
    NEW_ALT_EVT = 2
    LAND_EVT = 4

    MAX_ROTOR_CHANGE = 400.0
    MAX_RATE = 0.03
    MAX_ACCEL = 0.0002

    trgRate = 0.09
    trgAccel = 0.0002

    trg = 0.0
    act = 0.0
    tol = 1.0
    rate = 0.0
    accel = 0.0
    prevAccel = 0.0

    actRotSpd = 0.0
    desRotSpd = 0.0
    prevSpd = actRotSpd

    lastUpdate = time.time_ns()
    lastStamp = time.time_ns()
    
    NUM_SAMP = 15
    smShare = 1.0 / NUM_SAMP
    lgShare = 1.0 - smShare
    
    state = GND_ST
    
    eventQ = queue.Queue()

    zeroAccRotSpd = None
    zeroSpdRotSpd = None
    
    leave = None
    handle = None
    firstTick = True

    dS_dA = 250000.0 #change is rotor speed vs change in acceleration
    slowDownAlt = 0.0
    prevDeltaAlt = 0.0

    def dump(self,source):
        self.db(f"{source:10}, alttrg: {self.trg: 3.4f}, altact: {self.act: 3.4f}, altrate: {self.rate: 3.4f}, altaccel: {self.accel: 3.8f}, act rot: {self.actRotSpd: 3.4f}, des rot: {self.desRotSpd: 3.4f}, ds/da: {self.dS_dA: 3.4f},")
        pass


    def newAltEvt(self):
        if abs(self.act) < 0.001:
            self.setMainRotorSpeed(360.0,checkMax=False)
        else:
            share = self.kickShare()
            self.setMainRotorSpeed(self.desRotSpd + share)
        dA = self.getDeltaAlt()
        dAShare = 0.1 * dA
        self.slowDownAlt = self.trg - dAShare
        self.db(f" ========================== dA: {dA: 3.4f}, dAShare: {dAShare: 3.4f}, trg: {self.trg}, thresh: {self.slowDownAlt: 3.4f}")

    def altChgHndl(self):
        rt = self.rate
        ac = self.accel
        dA = self.getDeltaAlt()
        sign = 1.0
        if dA < 0.0:
            sign = -1.0
        trgRt = sign * self.MAX_RATE
        trgAc = sign * self.MAX_ACCEL
        dRt = trgRt - rt
        dAc = trgAc - ac
        
        if abs(dA) <= self.tol: #abs(self.act - self.slowDownAlt) <= 1.0: # slightly OOT, transition to locking it in place
            wh = "in tol, OK"
            self.sendEvent(self.AT_ALT_EVT)
        else:
            wh = self.controlRateAndAccel(dRt, dAc, trgRt, trgAc)

        #self.db(f"{wh} dA: {dA: 3.4f}, ac: {ac: 3.9f}, rt: {rt: 3.6f}")

    def holdAltHndl(self):
        rt = self.rate
        ac = self.accel
        dA = self.getDeltaAlt()
        #stabilze rates first
        if abs(dA) >= 3. * self.tol: # slightly OOT, transition to locking it in place
            wh = "================== OOT, kicking down "
            sign = 1.0
            if dA < 0.0:
                sign = -1.0
            trgRt = sign * self.MAX_RATE * 0.9
            trgAc = sign * self.MAX_ACCEL
            dRt = trgRt - rt
            dAc = trgAc - ac
            wh += self.controlRateAndAccel(dRt, dAc, trgRt, trgAc)
        elif abs(rt) >= 0.005 or abs(ac) >= 0.00001 and abs(dA) <= self.tol:
            wh = " rates are not zero "
            trgRt = 0.0
            trgAc = 0.0
            dRt = trgRt - rt
            dAc = trgRt - ac
            wh += self.controlRateAndAccel(dRt, dAc, trgRt, trgAc)

        #self.db(f"{wh} dA: {dA: 3.4f}, ac: {ac: 3.9f}, rt: {rt: 3.6f}")

    def controlRateAndaccelAlt(self, dRt, dAc, trgRt, trgAc):
        wh = ""
        '''
        Control altitude, only adjust things if below the max rate and below max accel.
        '''     
        dA = self.getDeltaAlt()
        prevDA = self.prevDeltaAlt
        ac = self.accel
        rt = self.rate
        kick = 0.0
        if dA < prevDA:
            wh = " gong the write way "
            if abs(dRt) > 0.005:
                wh += " rate OOT: "
            else:
                wh += " rate OK: "
                if abs(dAc) > 0.0001:
                    wh += " zero accel "
        else:
            wh += " going wrong way, flip accel "

        self.setMainRotorSpeed(self.desRotSpd + kick)

        self.db(f" kick: {kick: 3.4f}, desRot: {self.desRotSpd: 3.4f}, dA: {dA: 3.4f}, prevDA: {prevDA: 3.4f}, dRt: {dRt: 3.6f}, dAc: {dAc: 3.8f} =================================== {wh}")



    '''
    this attempts to figure out if rate and accel are correct to get us to target
    The logic is not correct, needs to be fixed
    '''
    def controlRateAndAccelAtt2(self,dRt, dAc, trgRt, trgAc, tol=0.00000001):
        kick = 0.0
        rt = self.rate
        ac = self.accel
        isAccel = (rt > 0.0 and ac > 0.0) or (rt < 0.0 and ac < 0.0)
        isDecel = (rt > 0.0 and ac < 0.0) or (rt < 0.0 and ac > 0.0)
        isConst = abs(rt) > 0.005 and abs(ac) <= 0.00001
        accOk = abs(dAc) < 0.00001
        if abs(dRt) > 0.003:
            wh = "Rate OOT "
            if dRt > 0.0:
                wh += " going towards rate "
                if isDecel:
                    wh += "need to accel "
                    if True: #abs(ac) < self.MAX_ACCEL:
                        wh += "not a max accel "
                        kick = 10.0 * dRt
                    else:
                        wh += " at max accel "
                else:
                    wh += " mv towards trg"
            if dRt < 0.0:
                wh = " overshot "
                if isAccel:
                    wh += " need to decel "
                    if True: #abs(ac) < self.MAX_ACCEL:
                        wh += " not at max decel "
                        kick = 10. * dRt
                    else:
                        wh += " at max decel"
                else:
                    wh += " mv towards trg"
        elif not isConst:
            #at rate, kill accel
            wh = "at rate, kill accel"
            kick = 100.0 * (0.0 - ac)
        self.setMainRotorSpeed(self.desRotSpd + kick)
        self.db(f"kick: {kick: 3.4f} spd: {self.desRotSpd: 3.4f}, rt: {rt: 3.6f}, acc: {ac: 4.9f}, dRt: {dRt: 3.8f}, dAc: {dAc: 3.9f},                          =======================  {wh}")
                
    '''
    this uses a constant reference speed to adjust rotor speed
    problem: the reference speed changes with changning mass, there is no way to figure it out.
    '''
    def controlRateAndAccelConst(self,dRt, dAc, trgRt, trgAc, tol=0.00000001):
        spd = self.desRotSpd
        ac = self.accel
        if self.zeroAccRotSpd is not None: spd = 0.983 * self.zeroAccRotSpd
        
        spd = 352.0 #this should reduce as the mass reduces, how to track it?
        corrConst = 0.05 * self.dS_dA
        corrConst = 2000.0
        dA = self.getDeltaAlt()
        wh = ""
        if abs(dRt) <= 0.005:
            wh = "rate in tol, accel to zero "
            trg = 0.0
            dAc = trg - ac
            rtCtl = dAc
            tol = 0.00001
            corrConst = 2000.0
            #if abs(rtCtl) < 0.00002:
            #    corrConst *= 2
        else:
            wh = "rate OOT, "
            rtCtl = dRt
            corrConst = math.sqrt(corrConst)
            trg = trgRt
            tol = 0.005
            corrConst = 1400.0
            #if abs(rtCtl) < 0.0002:
            #    corrConst *= 2
        '''
        if dAc is zero or is opposite of the dRt and dRt is not zero, correct
        otherwise keep it as is.
        '''
        rotSpd = spd
        if abs(rtCtl) > tol: # outside of 10% of max rate
            wh += f"rate not at target, "
            sign = 1.0 if rtCtl >= 0.0 else -1.0
            kick = corrConst * rtCtl
            #acKick = self.desRotSpd + sign * corrConst * math.log(abs(rtCtl),0.5)
            rotSpd = spd + kick
            
            if rotSpd < 0.0:
                rotSpd = spd - 20.0
            elif rotSpd >= 400.0:
                rotSpd = 399.9 # self.actRotSpd + 0.98 * self.MAX_ROTOR_CHANGE
            
            self.setMainRotorSpeed(rotSpd) #self.desRotSpd + acKick)
            wh += f"corrected, kick {kick: 3.4f}"

        self.db(f"rtCtl: {rtCtl: 3.9f}, trg: {trg:3.8f}, rotSpd: {rotSpd: 3.4f} zas: {spd: 3.4f}, cc:{corrConst: 3.5f}      ======================= {wh}")
        return wh


    def outOnGndHndl(self):
        self.setMainRotorSpeed(300.0)

    StateHandlers = {
        GND_ST: (None, None, outOnGndHndl),
        ALT_CHG_ST: (None, altChgHndl, None),
        AT_ALT_ST: (None, holdAltHndl, None),
    }

    
    StateMachine = {
        GND_ST: { 
            TAKE_OFF_EVT: (ALT_CHG_ST, None),
            AT_ALT_EVT: (AT_ALT_ST, None),
            NEW_ALT_EVT: (ALT_CHG_ST, newAltEvt),
        },
        ALT_CHG_ST: { 
            AT_ALT_EVT: (AT_ALT_ST, None),
            LAND_EVT: (GND_ST, None),
            NEW_ALT_EVT: (ALT_CHG_ST, newAltEvt),
        },
        AT_ALT_ST: { 
            NEW_ALT_EVT: (ALT_CHG_ST, newAltEvt),
            LAND_EVT: (ALT_CHG_ST, None),
        },
    }

    def __init__(self):
        super().__init__(self.TAG, self.DBG_MASK)
        self.state = self.GND_ST

    def tick(self, act, spd, _):
        now = time.time_ns()
        deltaT = now - self.lastUpdate
        self.dt = (deltaT) * 0.00000001
        if deltaT > 90.0e6:
            self.updateRates(act)
            self.act = act
            self.actRotSpd = spd
            if abs(self.rate) <= 0.000001 and abs(self.accel) <= 0.00000001 and self.act > 0.0: self.zeroSpdRotSpd = self.actRotSpd
            if abs(self.accel) <= 0.00000001 and self.act > 0.0: self.zeroAccRotSpd = self.actRotSpd
            if abs(self.actRotSpd - self.desRotSpd) > 0.1 and self.desRotSpd <= 400.0:
                self.dump("WAIT")
            else:
                if self.handle is not None:
                    self.handle(self)
                    self.dump("TICK")
            self.next()
            self.lastUpdate = now
            self.prevDeltaAlt = self.getDeltaAlt()
        return self.desRotSpd
    
    def updateRates(self,act):
        rate = (act - self.act) / self.dt
        rateAvg = self.rate * self.lgShare + rate * self.smShare
        accel = (rateAvg - self.rate) / self.dt
        accelAvg = self.accel * self.lgShare + accel * self.smShare
        self.rate = rateAvg
        self.accel = accelAvg

    def setTarget(self,trg, evt = True):
        self.trg = trg
        if evt:
            self.sendEvent(self.NEW_ALT_EVT)
        dActAlt = self.getDeltaAlt()
        if dActAlt > 0.0:
            self.trgRate = self.MAX_RATE
            self.trgAccel = self.MAX_ACCEL
        else:
            self.trgRate = -self.MAX_RATE
            self.trgAccel = -self.MAX_ACCEL

    def getDeltaAlt(self):
        return self.trg - self.act
    
    def setMainRotorSpeed(self, spd, checkMax = True):
        dSpd = self.desRotSpd - spd
        if (abs(dSpd) <= self.MAX_ROTOR_CHANGE and spd > 0.0 and spd <= 400.0) or not checkMax:
            self.lastChange = time.time_ns()
            try:
                spNow = self.actRotSpd
                spPrev = self.prevSpd
                acNow = self.accel
                acPrev = self.prevAccel
                dS = spNow - spPrev
                dA = acNow - acPrev
                dS_dA = abs((dS) / (dA))
                self.dS_dA = self.lgShare * self.dS_dA + self.smShare * dS_dA
                self.prevAccel = acNow
                self.prevSpd = spNow
                dza = acNow * self.dS_dA + self.desRotSpd
                #dS_dA = abs(self.actRotSpd / self.accel)
                self.db(f" =================================   ps: {spPrev: 3.4f} - cs: {spNow: 3.4f} = ds: {dS: 3.4f}, pa: {acPrev: 3.8f} - ca: {acNow: 3.8f} = dA: {dA: 3.10f}, ds/da: {dS_dA: 3.4f}, dza: {dza: 3.5f}")
            except:
                dS_dA = self.dS_dA
            
            self.desRotSpd = spd

    def rotorSped(self):
        return self.desRotSpd
    
    def kickShare(self):
        return 2.0 * self.getDeltaAlt()


