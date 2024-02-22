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
    TEST_ST = 110

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

    def pv(self, w, v):
        return f"({w:6}: ({v.x: 3.4f}, {v.y: 3.4f}, {v.z: 3.4f})"

    def dump(self,source):
        cp = self.pv("cur", self.curPos)
        tp = self.pv("trg", self.trgPos)
        dp = self.calcDistToTarget()
        self.db(f"{source:10}, {cp}, {tp}, dist: {dp:3.4f},facing: {self.velCtrl.facing:3.4f},\
 head: {self.velCtrl.velocityHeading:3.4f}, speed: {self.velCtrl.speed: 3.4f},\
 maxAccel: {self.maxAccel: 3.4f}, trgHdg: {self.trgHdg: 3.4f}")

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
        trgHdg = self.calcTargetHeading()
        self.headCtrl.setHeading(trgHdg)
        self.trgHdg = trgHdg

    def altChHndl(self):
        if self.curPos.getZ() >= (self.trgPos.getZ() - 15.0): #above certain safe hight
            self.sendEvent(self.LEVEL_EVT)
        else:
            #TODO check if alt changes towards the goal...
            self.db(f"Not at alt, waiting")
            if abs(self.altCtrl.trg - self.trgPos.z) > 0.1:
                self.altCtrl.setTarget(self.trgPos.z)
        _,_, mv = self.canMove()
        if mv:
            self.inAccelHndl()
            pass

    def inTurnHndl(self):
        trgHdg = self.calcTargetHeading()
        self.headCtrl.setHeading(trgHdg)
        self.trgHdg = trgHdg

    def turnHndl(self):
        trgHdg = self.calcTargetHeading()
        dist = self.calcDistToTarget()
        turnRt = abs(self.headCtrl.rotRate)
        trgHdg, turnRt, move = self.canMove()
        what = "check for heading target "
        if abs(trgHdg - self.headCtrl.trg) > self.headCtrl.tol and self.headCtrl.state == self.headCtrl.AT_HEAD_ST:
            self.inTurnHndl()
        what = "Waiting for direction "
        if move or dist < 4.0:
            what = "At heading, going to location "
            self.sendEvent(self.START_MOVE_EVT)
        
        self.db(f"{what}> headT: {trgHdg:3.4f}, actH: {self.headCtrl.act:3.4f}, rate: {turnRt:3.4f}, dist: {dist:3.4f}")
    
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
        stopDist = 1.06 * ((vel / acc) ** 2)
        
        if self.wentTooFar():
            what = " Went too far, stop, turn around"
            #reset went too far, before reacting
            self.deltaPos = self.calcDistToTarget() + 1.0
            self.sendEvent(self.DIR_EVT)

        elif distR < self.decelDist:
            what = "Less than half remain: "
            if distR < stopDist:
                #time to decelerate
                self.sendEvent(self.DECEL_EVT)
                what = "DONE. Start Decelerating "
        self.db(f"{what}> distR: {distR:3.4f}, prevD: {self.deltaPos: 3.4f}, halfway: {self.decelDist:3.4f}, stopDist: {stopDist:3.4f}")

    def inDecelHndl(self):
        self.velCtrl.setSpeed(0.0)
        self.altCtrl.setTarget(30.0)

    def decelHndl(self):
        what = "Wating to decelerate and stop"
        distR = self.calcDistToTarget()
        desHdg = self.calcTargetHeading()

        stopped = abs(self.velCtrl.speed) < 0.005 and abs(self.velCtrl.actTilt) < 0.095 # and self.velCtrl.actTilt > 0.0
        if stopped:
            what = " Stopped, checking "
            if self.wentTooFar(): #distance increased by whole unit
                what += " Went too far, stop, turn around"
                self.deltaPos = self.calcDistToTarget() + 1.0
                self.sendEvent(self.DIR_EVT)

            elif abs(self.velCtrl.speed) < 0.03:
                #TODO: tighten this
                if abs(distR) < 0.7:
                    self.sendEvent(self.LAND_EVT)
                    what += "DONE. Close, Landing "
                else:
                    self.maxAccel = self.MIN_ACCEL
                    if abs(desHdg - self.headCtrl.act) > 0.2:
                        what += "Need to turn around "
                        self.sendEvent(self.DIR_EVT)
                    else:
                        what += "Not close enough, need to adjust "
                        self.sendEvent(self.ACCEL_EVT)
        self.db(f"{what}> distT: {distR:3.4f}, prevD: {self.deltaPos: 3.4f}, speed: {self.velCtrl.speed:3.4f}, tilt: {self.velCtrl.actTilt:3.4f},  hdg: {self.headCtrl.act:3.4f}, trgHdg: {desHdg:3.4f}")

    def inDecHndl(self):
        self.altCtrl.setTarget(0.0)

    def decHndl(self):
        wh = "Wating for zero alt "
        if self.curPos.z < 0.2 and abs(self.altCtrl.altRate) < 0.1:
            wh = "Landed!"
            self.sendEvent(self.DROP_EVT)

        self.db(f"{wh}: alt: {self.curPos.z: 3.4f}, altRt: {self.altCtrl.altRate: 3.4f}")

    def inLandedHndl(self):
        self.altCtrl.setTarget(0.1)

    def landedHndl(self):
        if self.curPos.z < 0.5:
            self.sendEvent(self.DROP_EVT)
            
    def inHoverHndl(self):
        self.headCtrl.setHeading(self.velCtrl.velocityHeading)
        
    def hoverHndl(self):
        faceFwd = self.velCtrl.isFwd()
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

    def altTests(self):
        alts = [70, 90, 30, 65, 110, 30, 45, 0.2, 70]
        idx = 0
        alt = alts[idx]
        preLt = alt

        now = time.time_ns()
        deltaT = now - self.startStamp
        if idx == 0:
            #self.velCtrl.setSpeed(0.4)
            self.altCtrl.setTarget(alt)
            preAlt = alt
            idx += 1
        elif (idx < len(alts) and abs(self.altCtrl.trg - self.altCtrl.act) < self.altCtrl.tol) and self.altCtrl.state == self.altCtrl.AT_ALT_ST:
            self.altCtrl.setTarget(alts[idx])
            idx += 1

    def headTests(self):
        vals = [290,0.0, 90, 180, 45, 272, 70, 45, 355, 270, 273, 272, 70, 90, 180, 268, 100, 180, 45, 355, 270, 273, 272, 0.0]

        now = time.time_ns()
        deltaT = now - self.startStamp
        idx = self.idx

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
        self.idx = idx

    def testHndl(self):
        self.headTests()

    StateHandlers = {
        INIT_ST: (None, initHndl, None),
        ON_GND_ST: (inGndHndl, gndHndl, None),
        ALT_CHANGE_ST: (inAltChgHndl, altChHndl, None),
        TURNING_ST: (inTurnHndl, turnHndl, None),
        ACCEL_ST: (inAccelHndl, accelHndl, None),
        APPROACH_ST: (None, None, None),
        DECEL_ST: (inDecelHndl, decelHndl, None),
        HOVER_ST: (inHoverHndl, hoverHndl, None),
        DECEND_ST: (inDecHndl, decHndl, None),
        LANDED_ST: (inLandedHndl, landedHndl, None),
        DELIVER_ST: (None, None, None),
        TEST_ST: (None, testHndl, None),
    }

    StateMachine = {
        INIT_ST: {
                    GO_EVT: (ON_GND_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (INIT_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (INIT_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (INIT_ST, None),
                    TEST_EVT: (TEST_ST, None),
                },
        ON_GND_ST: {
                    GO_EVT: (ALT_CHANGE_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (INIT_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (INIT_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                    TEST_EVT: (TEST_ST, None),
                },
        ALT_CHANGE_ST: {
                    GO_EVT: (INIT_ST, None),
                    LEVEL_EVT: (TURNING_ST, None),
                    DIR_EVT: (INIT_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (INIT_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        TURNING_ST: {
                    GO_EVT: (INIT_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (TURNING_ST, None),
                    START_MOVE_EVT: (ACCEL_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (INIT_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        ACCEL_ST: {
                    GO_EVT: (INIT_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (TURNING_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (DECEL_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (INIT_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        APPROACH_ST: {
                    GO_EVT: (INIT_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (INIT_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (INIT_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        DECEL_ST: {
                    GO_EVT: (INIT_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (TURNING_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (ACCEL_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (DECEND_ST, None),
                    DROP_EVT: (INIT_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        HOVER_ST: {
                    GO_EVT: (ALT_CHANGE_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (INIT_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (INIT_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        DECEND_ST: {
                    GO_EVT: (INIT_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (INIT_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (LANDED_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (HOVER_ST, None),
                },
        LANDED_ST: {
                    GO_EVT: (INIT_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (INIT_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (DELIVER_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (INIT_ST, None),
                },
        DELIVER_ST: {
                    GO_EVT: (ALT_CHANGE_ST, None),
                    LEVEL_EVT: (INIT_ST, None),
                    DIR_EVT: (INIT_ST, None),
                    START_MOVE_EVT: (INIT_ST, None),
                    ACCEL_EVT: (INIT_ST, None),
                    FLY_EVT: (INIT_ST, None),
                    DECEL_EVT: (INIT_ST, None),
                    LAND_EVT: (INIT_ST, None),
                    DROP_EVT: (INIT_ST, None),
                    NULL_EVT: (INIT_ST, None),
                    HOVER_EVT: (INIT_ST, None),
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
        return self.altCtrl.rotSpd, self.headCtrl.desRotSpd, self.velCtrl.desTilt

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
    
    def canMove(self):
        trgHdg = self.calcTargetHeading()
        isStable = self.headCtrl.isStable()
        res = abs(trgHdg - self.headCtrl.act) <= self.headCtrl.tol and isStable
        return trgHdg, abs(self.headCtrl.rotRate), res

    def wentTooFar(self):
        distR = self.calcDistToTarget()
        res = distR > (self.deltaPos + 0.5)
        return res


if __name__ == '__main__':
    pos = ApachiPos()
    pos.setPosition(Vec3(23,11,70))
    pos.tick(Vec3(0,0,0), 0.9, 0.0, 0.0, 0.0, 0.0)

