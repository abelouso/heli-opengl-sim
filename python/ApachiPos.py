#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec4

import math
import queue
import inspect
import time
from BaseStateMachine import *
from ApachiAlt import *
from ApachiHead import *
from ApachiVel import *

class ApachiPos(BaseStateMachine):
    INIT_ST = 100
    ON_GND_ST = 101
    ALT_CHANGE_ST = 102
    TURNING_ST = 103
    ACCEL_ST = 104
    APPROACH_ST = 105
    DECEL_ST = 106
    HOVER_ST = 110
    DECEND_ST = 107
    LANDED_ST = 108
    DELIVER_ST = 109
    TEST_ST = 111

    GO_EVT = 150
    LEVEL_EVT = 151
    DIR_EVT = 152
    START_MOVE_EVT = 153
    ACCEL_EVT = 154
    FLY_EVT = 155
    DECEL_EVT = 156
    LAND_EVT = 157
    DROP_EVT = 158
    NULL_EVT = 159
    HOVER_EVT = 160
    TEST_EVT = 161

    POS_TOL = Vec3(0.5, 0.5, 0.5)
    POS_MAG_TOL = 1.0
    MAX_ACCEL = 0.088 #empricially defined
    MIN_ACCEL = 0.0001 # not to divied by zero

    eventQ = queue.Queue()
    leave = None
    handle = None
    
    dt = 0
    lastStamp = time.time_ns()
    lastChange = lastStamp
    state = INIT_ST
    firstTick = True

    curPos = Vec3(0, 0, 0)
    prevPos = Vec3(0, 0, 0)
    trgPos = Vec3(0, 0, 0)

    altCtrl = ApachiAlt()
    headCtrl = ApachiHead()
    velCtrl = ApachiVel()

    decelDist = 1000.0

    maxAccel = MIN_ACCEL

    trgHdg = 0.0
    deltaPos = 0.0

    id = 1000

    idx = 0
    idxAlt = 0
    idxVel = 0
    idxHdg = 0
    testAltStamp = time.time_ns()
    testVelStamp = time.time_ns()
    dropOffAlt = -0.4

    sock = None

    def pv(self, w, v):
        return f"{w:6}:({v.x: 3.4f}, {v.y: 3.4f}, {v.z: 3.4f})|"

    def dump(self,source):
        cp = self.pv("cur", self.curPos)
        tp = self.pv("trg", self.trgPos)
        dp = self.calcDistToTarget()
        self.db(f"{source:10}, {cp}, {tp}, dist: {dp:3.4f},facing: {self.velCtrl.facing:3.4f},"\
                f"head: {self.velCtrl.velocityHeading:3.4f}, speed: {self.velCtrl.speed: 3.6f},"\
                f"maxAccel: {self.maxAccel: 3.4f}, trgHdg: {self.trgHdg: 3.4f}")

    def initHndl(self):
        if self.curPos.getZ() < 0.1:
            self.sendEvent(self.GO_EVT)

    def inGndHndl(self):
        self.altCtrl.setTarget(self.trgPos.z)

    def gndHndl(self):
        if self.curPos.getZ() > 0.1:
            self.db(f"Self lifted off...")
            self.sendEvent(self.GO_EVT)
        else:
            self.db(f"Waiting to lift off...")

    def inAltChgHndl(self):
        self.maxAccel = self.MIN_ACCEL
        if False: #self.velCtrl.isStopped():
            trgHdg = self.calcTargetHeading()
            self.headCtrl.setHeading(trgHdg)
            self.trgHdg = trgHdg
        else:
            self.velCtrl.setSpeed(0.0)

    def altChHndl(self):
        if self.curPos.getZ() >= (self.trgPos.getZ() - 15.0): #above certain safe hight
            self.sendEvent(self.LEVEL_EVT)
        else:
            #TODO check if alt changes towards the goal...
            self.db(f"Not at alt, waiting")
            if abs(self.altCtrl.trg - self.trgPos.z) > 0.1:
                self.altCtrl.setTarget(self.trgPos.z)
        _,_, mv = self.canMove(self.headCtrl.tol)
        if mv:
            #self.inAccelHndl()
            pass

    def inTurnHndl(self):
        trgHdg = self.calcTargetHeading()
        self.headCtrl.setHeading(trgHdg)
        self.trgHdg = trgHdg
        self.turnStart = time.time_ns()
        self.velCtrl.sendEvent(self.velCtrl.IDLE_EVT)

    def turnHndl(self):
        trgHdg = self.calcTargetHeading()
        dist = self.calcDistToTarget()
        turnRt = abs(self.headCtrl.rotRate)
        trgHdg, turnRt, move = self.canMove(1.0 * self.headCtrl.tol)
        what = "check for heading target "
        deltaT = time.time_ns() - self.turnStart
        tooLong = deltaT >= 3000.0e6 #a second?
        if abs(trgHdg - self.headCtrl.trg) > self.headCtrl.tol and self.headCtrl.state == self.headCtrl.AT_HEAD_ST and tooLong:
            self.headCtrl.setHeading(trgHdg)
            pass
        what = "Waiting for direction "
        if move or dist < 4.0:
            what = "At heading, going to location "
            self.sendEvent(self.START_MOVE_EVT)
        elif not self.velCtrl.isStopped():
            what = "Not stopped, go to hover"
            self.sendEvent(self.HOVER_EVT)
        
        self.db(f"{what}> headT: {trgHdg:3.4f}, actH: {self.headCtrl.act:3.4f}, rate: {turnRt:3.4f}, dist: {dist:3.4f}")

    def outTurnHndl(self):
        self.velCtrl.sendEvent(self.velCtrl.BUSY_EVT)
    
    def inAccelHndl(self):
        if self.velCtrl.trg > 0.031:
            self.db(f"Already moving at {self.velCtrl.speed:3.4f}, with trg: {self.velCtrl.trg:3.4f}")
        else:
            #calcluate motion profiles to arrive to x,y
            dist = self.calcDistToTarget()
            #speed directly proprotional to distance to target
            trgSpd = 0.0015 * dist + 0.25 #ensure minimum speed
            #let's make acceleration and deceleration zones, cut them in half
            self.decelDist = 0.525 * dist
            self.velCtrl.setSpeed(trgSpd)
            self.db(f"Distance to target: {dist:3.4f}, speed: {trgSpd:3.4f}")

    def accelHndl(self):
        distR = self.calcDistToTarget()
        self.trgHdg = self.calcTargetHeading()
        what = "Acceleraing "
        vel = self.velCtrl.speed
        acc = self.maxAccel
        acc = self.velCtrl.MAX_ACCEL
        stopDist = 0.06 * ((vel / acc))
        
        if not self.velCtrl.isToTarget(self.trgHdg) and distR >= 12.0:
            self.velCtrl.setSpeed(0.0)
            if self.velCtrl.isStopped():
                if distR <= 3.0:
                    self.sendEvent(self.LAND_EVT)
                else:
                    self.sendEvent(self.HOVER_EVT)

        elif distR < self.decelDist:
            what = "Less than half remain: "
            if distR < stopDist:
                #time to decelerate
                self.sendEvent(self.DECEL_EVT)
                what = "DONE. Start Decelerating "
        self.db(f"{what}> distR: {distR:3.4f}, prevD: {self.deltaPos: 3.4f}, halfway: {self.decelDist:3.4f}, stopDist: {stopDist:3.4f}")

    def inDecelHndl(self):
        self.velCtrl.setSpeed(0.0)
        #self.altCtrl.setTarget(30.0)

    def decelHndl(self):
        what = "Wating to decelerate and stop"
        distR = self.calcDistToTarget()
        desHdg = self.calcTargetHeading()
        withInDist = distR <= 8.0
        needToTurn = abs(desHdg - self.headCtrl.act) and withInDist
        spdTol = 0.003 if needToTurn else 0.0096
        lowSpd = abs(self.velCtrl.speed) < spdTol
        noTilt = abs(self.velCtrl.actTilt) < 0.095
        stopped = lowSpd and noTilt # and self.velCtrl.actTilt > 0.0
        if stopped:
            what = " Stopped, checking "
            if self.wentTooFar(): #distance increased by whole unit
                what += " Went too far, stop, turn around"
                #self.deltaPos = self.calcDistToTarget() + 1.0
                #self.sendEvent(self.DIR_EVT)
                self.velCtrl.setSpeed(-0.03)

            elif abs(self.velCtrl.speed) < 0.04:
                #TODO: tighten this
                if withInDist:
                    self.sendEvent(self.LAND_EVT)
                    what += "DONE. Close, Landing "
                else:
                    self.maxAccel = self.MIN_ACCEL
                    if needToTurn > 0.2:
                        what += "Need to turn around "
                        self.sendEvent(self.DIR_EVT)
                    else:
                        what += "Not close enough, need to adjust "
                        self.sendEvent(self.ACCEL_EVT)
        elif distR < 5.0:
            what += " adjusting position"
            self.velTowardsPos()
            if distR < 2.0:
                self.sendEvent(self.LAND_EVT)
                what += "Done, landing...."

        self.db(f"{what}> distT: {distR:3.4f}, prevD: {self.deltaPos: 3.4f}, "\
                f"speed: {self.velCtrl.speed:3.4f}, tilt: {self.velCtrl.actTilt:3.4f},  "\
                f"hdg: {self.headCtrl.act:3.4f}, trgHdg: {desHdg:3.4f}, noSpd: {lowSpd}, noTilt: {noTilt},")

    def inDecHndl(self):
        self.altCtrl.setTarget(self.dropOffAlt)

    def decHndl(self):
        wh = "Wating for zero alt "
        dist = self.calcDistToTarget()
        dDp = self.deltaPos - dist
        self.velTowardsPos()
        if self.curPos.z < 0.2 and abs(self.altCtrl.altRate) < 0.1:
            wh = "Landed!"
            self.sendEvent(self.DROP_EVT)

        self.db(f"{wh}: alt: {self.curPos.z: 3.4f}, altRt: {self.altCtrl.altRate: 3.4f}, DDP: {dDp: 3.4f}")

    def delHndl(self):
        dist = self.velTowardsPos()
        landed = self.isLanded()
        if dist > 1.0 and landed:
            self.altCtrl.setTarget(1.0)
            self.sendEvent(self.FLY_EVT)
            self.db(f"DEBUG1: landed too far, take off")
        #if dist < 0.8 and self.altCtrl.act < 0.2:
        #    self.db(f"Setting negative alt target to land")
        #    self.altCtrl.setTarget(-0.3)


    def inLandedHndl(self):
        self.altCtrl.setTarget(self.dropOffAlt)

    def landedHndl(self):
        self.velTowardsPos()
        if self.curPos.z < 0.5:
            self.sendEvent(self.DROP_EVT)
            
    def inHoverHndl(self):
        self.headCtrl.setHeading(self.velCtrl.velocityHeading)

    def outDelHndl(self):
        self.altCtrl.setMainRotorSpeed(400.0)
        
    def hoverHndl(self):
        faceFwd = self.velCtrl.isAlongPath()
        stable = self.headCtrl.isStable()
        stopped = self.velCtrl.isStopped()
        wh = "In hover"
        if stable and not faceFwd:
            #adjust it again
            self.headCtrl.setHeading(self.velCtrl.velocityHeading)
            wh = "Heading is not correct"
        elif faceFwd and stopped:
            #we are stable, facing forward and stopped, ready to move
            wh = "all stable, get out"
            self.sendEvent(self.GO_EVT)
        self.db(f"{wh} faceFwd: {faceFwd}, stable: {stable}, stopped: {stopped}")

    def aprHndl(self):
        landed = self.isLanded()
        if not landed:
            self.altCtrl.setTarget(self.dropOffAlt)
            self.sendEvent(self.DROP_EVT)

    def altTests(self):
        alts = [170, 0.2, 40, 20, 65, 110, 30, 45, 0.0, 70, 0.0, 20.0]

        now = time.time_ns()
        atAlt = self.altCtrl.state == self.altCtrl.AT_ALT_ST
        inTol = abs(self.altCtrl.trg - self.altCtrl.act) < 2.0 * self.altCtrl.tol
        moreAlts = self.idxAlt < len(alts)
        if atAlt and inTol and self.testAltStamp is None:
            self.testAltStamp = now
        if self.testAltStamp is not None:
            atTime = (now - self.testAltStamp) > 20.0e9
        else:
            atTime = False

        self.db(f" {moreAlts} and {inTol} and {atAlt}")
        if self.idxAlt == 0:
            #self.velCtrl.setSpeed(0.4)
            self.altCtrl.setTarget(alts[self.idxAlt])
            self.idxAlt += 1
            self.testAltStamp = None
        elif moreAlts and inTol and atAlt and atTime:
            self.altCtrl.setTarget(alts[self.idxAlt])
            self.db(f" ========================== ******************************************************** set new alt ")
            self.idxAlt += 1
            self.testAltStamp = None
        return self.idxAlt >= len(alts)
    
    def velTests(self):
        vals = [0.4, 0.0, 0.8, 0.0, -.7,-.4,0.0, -100.0]

        now = time.time_ns()
        atVel = True #self.velCtrl.state == self.velCtrl.MAINT_ST
        inTol = abs(self.velCtrl.trg - self.velCtrl.speed) <= self.velCtrl.tol
        moreVels = self.idxVel < len(vals)
        if atVel and inTol and self.testVelStamp is None:
            self.testVelStamp = now
        if self.testVelStamp is not None:
            atTime = (now - self.testVelStamp) > 25.0e9
        else:
            atTime = False

        self.db(f" atVel: {atVel}, inTol: {inTol}, moreVels: {moreVels}, atTime: {atTime}")
        newVal = None
        if moreVels: newVal = vals[self.idxVel]
        
        if self.idxVel == 0:
            if self.altCtrl.trg < 0.1:
                self.altCtrl.setTarget(70)
            elif self.altCtrl.act > 0.8 * self.altCtrl.trg:
                self.velCtrl.setSpeed(vals[self.idxVel])
                self.idxVel += 1
                self.db(f"Set initial velocity {newVal: 3.4f} ======================================= ")
        elif atVel and inTol and moreVels and atTime:
            if newVal < -50.0:
                #turn an go
                self.headCtrl.setHeading(45)
                newVal = 0.34
            self.velCtrl.setSpeed(newVal)
            self.db(f"Set next velocity {newVal: 3.4f} ======================================= {newVal:3.4f} ")
            self.idxVel += 1
            self.testVelStamp = None
        
        return self.idxVel >= len(vals)

    def headTests(self):
        vals = [290,0.0, 90, 180, 45, 272, 70, 45, 355, 270, 273, 272, 70, 90, 180, 268, 100, 180, 45, 355, 270, 273, 272, 0.0]

        now = time.time_ns()
        deltaT = now - self.startStamp
        idx = self.idxHdg

        if idx == 0:
            #self.velCtrl.setSpeed(0.4)
            if self.altCtrl.trg < 30:
                self.altCtrl.setTarget(150)
            if self.altCtrl.act > 5.0:
                self.headCtrl.setHeading(vals[idx])
                idx += 1
        elif idx < len(vals) and abs(self.headCtrl.trg - self.headCtrl.act) < self.headCtrl.tol and self.headCtrl.state == self.headCtrl.AT_HEAD_ST:
            self.headCtrl.setHeading(vals[idx])
            idx += 1
        self.idxHdg = idx
        return idx >= len(vals)
    
    
    def testHndl(self):
        #self.headTests()
        self.velTests()

    StateHandlers = {
        INIT_ST: (None, initHndl, None),
        ON_GND_ST: (inGndHndl, gndHndl, None),
        ALT_CHANGE_ST: (inAltChgHndl, altChHndl, None),
        TURNING_ST: (inTurnHndl, turnHndl, outTurnHndl),
        ACCEL_ST: (inAccelHndl, accelHndl, None),
        APPROACH_ST: (None, aprHndl, None),
        DECEL_ST: (inDecelHndl, decelHndl, None),
        HOVER_ST: (inHoverHndl, hoverHndl, None),
        DECEND_ST: (inDecHndl, decHndl, None),
        LANDED_ST: (inLandedHndl, landedHndl, None),
        DELIVER_ST: (None, delHndl, outDelHndl),
        TEST_ST: (None, testHndl, None),
    }

    StateMachine = {
        INIT_ST: {
                    GO_EVT: (ON_GND_ST, None),
                    TEST_EVT: (TEST_ST, None),
                },
        ON_GND_ST: {
                    GO_EVT: (ALT_CHANGE_ST, None),
                    LEVEL_EVT: (ON_GND_ST, None),
                    DIR_EVT: (ON_GND_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                    TEST_EVT: (TEST_ST, None),
                },
        ALT_CHANGE_ST: {
                    LEVEL_EVT: (TURNING_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        TURNING_ST: {
                    DIR_EVT: (TURNING_ST, None),
                    START_MOVE_EVT: (ACCEL_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        ACCEL_ST: {
                    DIR_EVT: (TURNING_ST, None),
                    DECEL_EVT: (DECEL_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        APPROACH_ST: {
                    DROP_EVT: (DELIVER_ST, None),
                },
        DECEL_ST: {
                    GO_EVT: (DECEL_ST, None),
                    LEVEL_EVT: (DECEL_ST, None),
                    DIR_EVT: (TURNING_ST, None),
                    START_MOVE_EVT: (DECEL_ST, None),
                    ACCEL_EVT: (ACCEL_ST, None),
                    FLY_EVT: (DECEL_ST, None),
                    DECEL_EVT: (DECEL_ST, None),
                    LAND_EVT: (DECEND_ST, None),
                    DROP_EVT: (DECEL_ST, None),
                    NULL_EVT: (DECEL_ST, None),
                    HOVER_EVT: (DECEL_ST, None),
                },
        HOVER_ST: {
                    GO_EVT: (ALT_CHANGE_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        DECEND_ST: {
                    DROP_EVT: (LANDED_ST, None),
                    HOVER_EVT: (DECEND_ST, None),
                },
        LANDED_ST: {
                    DROP_EVT: (DELIVER_ST, None),
                },
        DELIVER_ST: {
                    GO_EVT: (ALT_CHANGE_ST, None),
                    FLY_EVT: (APPROACH_ST, None),
                    TEST_EVT: (TEST_ST, None),
                },
        TEST_ST: {
            TEST_EVT: (INIT_ST, None),
        },
    }

    def __init__(self,id):
        super().__init__("ApachiPos",0x10)
        self.state = self.INIT_ST
        self.id = id
        self.startStamp = time.time_ns()

    def tick(self, actPos, actHdg, actMainRot, actTailRot, actTilt, dt):
        self.updateTimeStamp()
        alt = actPos.getZ()
        self.prevPos = self.curPos
        self.curPos = Vec3(actPos.x,actPos.y,actPos.z)
        self.altCtrl.tick(alt,actMainRot,dt)
        self.headCtrl.tick(actHdg,actTailRot,alt,dt)
        self.velCtrl.tick(actPos,actTilt,dt,alt,actHdg)
        if self.maxAccel < self.velCtrl.accel:
            self.maxAccel = self.velCtrl.accel
        #cap to prevent glitches
        #if self.maxAccel > self.MAX_ACCEL:
        #    self.maxAccel = self.MAX_ACCEL
        self.dump("TICK")
        if self.handle is not None:
            self.handle(self)
        self.next()
        now = time.time_ns()
        if (now - self.lastChange > 600e6):
            self.deltaPos = self.calcDistToTarget()
            self.lastChange = time.time_ns()
        return self.altCtrl.desRotSpd, self.headCtrl.desRotSpd, self.velCtrl.desTilt

    def setPosition(self, trg):
        if not self.pos3DInTol(trg, self.curPos):
            self.trgPos = trg
            self.sendEvent(self.GO_EVT)

    def pos3DInTol(self, pos1, pos2):
        diff = pos1 - pos2
        return (diff - self.POS_TOL).length() < self.POS_MAG_TOL
    
    def pos2DInTol(self, pos1, pos2):
        p12D = pos1.xy
        p22D = pos2.xy
        diff = p12D - p22D
        tol = self.POS_TOL.xy
        return (diff - tol).length() < self.POS_MAG_TOL
    
    def calcTargetHeading(self):
        p1 = self.trgPos.xy
        p2 = self.curPos.xy
        diff = (p1 - p2)
        trgHdg = math.degrees(math.atan2(diff.y,diff.x))
        if trgHdg < 0.0:
            trgHdg += 360.0
        return trgHdg

    def calcDistance(self,pos1,pos2):
        p1 = pos1.xy
        p2 = pos2.xy
        diff = (p2 - p1)
        return diff.length()

    def calcDistToTarget(self):
        return self.calcDistance(self.trgPos, self.curPos)
    
    def canMove(self, tol):
        trgHdg = self.calcTargetHeading()
        isStable = self.headCtrl.isStable()
        inTol = abs(trgHdg - self.headCtrl.act) <= tol
        self.db(f" sable: {isStable}, in tol: {inTol}")
        res = inTol and isStable
        return trgHdg, abs(self.headCtrl.rotRate), res

    def wentTooFar(self):
        distR = self.calcDistToTarget()
        res = abs(distR - self.deltaPos) >= 9.0
        return False
    
    def velTowardsPos(self):
        wh = "Wating for zero alt "
        dist = self.calcDistToTarget()
        dDp = self.deltaPos - dist
        trgHdg = math.radians(self.calcTargetHeading())
        myHdg =  math.radians(self.headCtrl.act)
        trgVec = Vec2(math.sin(trgHdg), math.cos(trgHdg))
        myVec = Vec2(math.sin(myHdg), math.cos(myHdg))
        dot = trgVec.dot(myVec)
        sign = 1.0 if dot > 0.0 else -1.0
        if dot == 0.0: sign = 0.0

        #if dist > 0.3:
        #    wh = "going "
        prop = 0.008 if sign >= 0.0 else 0.011
        spd = prop * abs(dist) * sign
        self.velCtrl.setSpeed(spd)
        #else:
        #    wh = "set zero vel"
        #    self.velCtrl.setSpeed(0.0)

        self.db(f"{wh}: dist: {dist: 3.4f}, DDP: {dDp: 3.4f}, dot: {dot: 3.5f}, sign: {sign: 3.4f}")
        self.db(f"DEBUG1: {prop: 3.4f} spd: {spd: 3.4f},")
        return dist

    def isLanded(self):
        landed = not base.myChoppers[self.id][1].takenOff
        return landed


if __name__ == '__main__':
    pos = ApachiPos()
    pos.setPosition(Vec3(23,11,70))
    pos.tick(Vec3(0,0,0), 0.9, 0.0, 0.0, 0.0, 0.0)

