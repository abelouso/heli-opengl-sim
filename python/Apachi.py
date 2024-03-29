#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode


import math
import queue
import time
from datetime import timedelta
import copy

from BaseObject import *
from StigChopper import *
from ApachiPos import *
from TravSalesman import *

class Apachi(StigChopper):
    startTime = time.time_ns()
    cruseAlt = 62
    fullTank = None
    rotAngle = 0.0
    optimalRouteIdxArr = None
    tsmObject = None
    tsmWps = None
    firstPack = True

    def __init__(self,id, pos, scale=0.2):
        StigChopper.__init__(self,id,pos,"Models/ArmyCopter", {}, "apachi")
        self.actor.setScale(scale,scale,scale)
        self.rotDir = 1.0
        self.actAngle = 0
        self.mainSpeed = 0.0
        self.tilt = 0.0
        self.tailSpeed = 0.0
        self.ctrl = ApachiPos(self.id,self.cruseAlt)
        self.ctrl.db("==== STARTING APACHI ====")
        #self.ctrl.sendEvent(self.ctrl.TEST_EVT)
        #self.ctrl.setPosition(Vec3(-100,-105,70))
        #self.ctrl.setPosition(Vec3(15.0,-11.00,70))
        self.spiny1 = None
        self.spiny2 = None
        for child in self.actor.children:
            self.findRotNodes(child, 0)
        
    def findRotNodes(self, nodepath, recurse_level):
        for child in nodepath.children:
            if not child is None:
                if nodepath.getName() == "Rotor":
                    self.spiny = nodepath
                self.ctrl.db("Name -- {}: {}".format((' ' * recurse_level), child.getName()))
                self.findRotNodes(child, recurse_level + 1)

    def findNearPos(self, myPos, wps):
        sz = len(wps)
        nearIdx = None
        nearPos = None
        pt = None
        if sz > 0:
            nearPos = wps[0]
            nearIdx = 0
            if sz > 1:
                idx = 0
                dist = 1e6
                for pos in wps:
                    deltaX = pos.x - myPos.x
                    deltaY = pos.y - myPos.y
                    curDistance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
                    self.ctrl.db(f" idx: {idx}, dist: {dist: 3.4f}")
                    if self.firstPack:
                        #print(f"wps.append(Vec3({pos.x}, {pos.y}, {pos.z}))")
                        self.ctrl.db(f"origSet :({pos.x},{pos.y},{pos.z})|")
                    if curDistance < dist:
                        nearPos = pos
                        dist = curDistance
                        nearIdx = idx
                        self.ctrl.db(f"New near: {dist:3.4f}, idx: {idx}")
                    idx += 1
        return nearIdx, nearPos

    def findNextPos(self,myPos):
        nxtIdx, nxtPos = self.findNearPos(myPos,self.targetWaypoints)
        #return nxtIdx, nxtPos
        #print(f"Closes: {nxtIdx}, at {nxtPos}")
        try:
            sz = len(self.targetWaypoints)
            if self.tsmObject is None:
                self.tsmWps = copy.deepcopy(self.targetWaypoints)
                lastPos = nxtPos
                self.tsmWps.remove(nxtPos)
                for _ in range(3):
                    _, toElim  = self.findNearPos(lastPos,self.tsmWps)
                    lastPos = toElim
                    self.tsmWps.remove(toElim)
                print(self.tsmWps)
                self.tsmObject = TravSalesman()
                self.tsmObject.determine(lastPos,self.tsmWps)
            #elif sz == 8:
            #    self.tsmWps = self.targetWaypoints[0:10]
            #    self.tsmWps.remove(nxtPos)
            #    self.tsmObject.determine(nxtPos,self.tsmWps)
            elif sz <= 11 and self.tsmObject.allDone():
                if not self.tsmObject.done:
                    self.tsmObject.finish()
                    for idx in range(len(self.tsmObject.idx)):
                        pos = self.tsmWps[self.tsmObject.idx[idx]]
                        self.ctrl.db(f"tsmpath :({pos.x},{pos.y},{pos.z})|")
                        #print(f"tsmpath :({pos.x},{pos.y},{pos.z})|")
                nxTmp = self.tsmObject.nextIndex()
                if nxTmp is not None:
                    nxtIdx = nxTmp
                    nxtPos = self.tsmWps[nxtIdx]
        except Exception as ex:  #revert to the clos
            print(f"Exception in findNexPos for next pos: {ex}")
        #print(f" nxtIDX: {nxtIdx}, at pos {nxtPos}")
        return nxtIdx, nxtPos

    def setWaypoints(self, wp):
        super().setWaypoints(wp)
        self.targetWaypoints = wp
        self.cargoIdx = 0
        myPos = base.gps(self.id)
        if self.firstPack:
            self.cargoIdx, pt = self.findNextPos(myPos)
            if pt is not None:
                self.ctrl.setPosition(Vec3(pt.x, pt.y, self.cruseAlt))
                self.ctrl.db(f"packages: {len(self.targetWaypoints)},")
                #del(self.targetWaypoints[self.cargoIdx])
                self.firstPack = False
        if self.fullTank is None:
            self.fullTank,_ = self.getRemFuel()
            
    def spinRotor(self, tick, rotSpd):
        aDelta = 0.0
        try:
            aDelta = rotSpd * 360.0 / (100000.0 * tick)
        except:
            aDelta = 0.0
        self.rotAngle += aDelta
        #if self.rotAngle > 360.0: self.rotAngle -= 360.0
        if self.spiny is not None:
            self.spiny.setHpr(Vec3(self.rotAngle, 0, 0))


    def update(self,dt,tick):
        StigChopper.update(self,dt,tick)

    def runLogic(self,dt,tick):
        StigChopper.runLogic(self,dt,tick)
        pos = base.gps(self.id)
        orient = base.transformations(self.id)
        hdng = orient.getX()
        #TODO: provide access to this
        actSpd = base.myChoppers[self.id][1].actMainRotorSpeed_RPM
        tailSpd = base.myChoppers[self.id][1].actTailRotorSpeed_RPM
        actTilt = base.myChoppers[self.id][1].actTilt_Degrees
        self.spinRotor(tick,actSpd)
        _,fp = self.getRemFuel()
        self.mainSpeed, self.tailSpeed, self.tilt = self.ctrl.tick(pos, hdng, actSpd, tailSpd, actTilt, dt, fp)
        base.requestSettings(self.id,self.mainSpeed,self.tilt,self.tailSpeed)
        if self.ctrl.velCtrl.state == self.ctrl.velCtrl.SIDE_ST and not self.ctrl.state == self.ctrl.HOVER_ST:
            #transition to however
            self.ctrl.sendEvent(self.ctrl.HOVER_EVT)
        if self.ctrl.state == self.ctrl.DELIVER_ST:
            if len(self.targetWaypoints) > 0:
                delviered = base.deliverPackage(self.id)
                if delviered:
                    self.ctrl.db(f"================== DELIVERED PACKAGE ===================== #{self.cargoIdx}")
                    self.cargoIdx, pt = self.findNextPos(pos)
                    if self.cargoIdx is None:
                        self.ctrl.db(f"packages: {len(self.targetWaypoints)},")
                        deltaT_s = pos.getW()
                        eltimeStr = timedelta(seconds=deltaT_s)
                        delStr = f"== APACHI DELIVERED ALL PACKAGES: in {eltimeStr}/ {deltaT_s}, returning to base..."
                        self.ctrl.db(f"DEBUG1 {delStr},")
                        print(delStr,flush=True)
                        if self.homeBase is not None:
                            self.ctrl.setPosition(Vec3(self.homeBase.x, self.homeBase.y, self.cruseAlt))
                            self.ctrl.sendEvent(self.ctrl.GO_EVT)
                        else:
                            self.ctrl.altCtrl.setMainRotorSpeed(0.0)
                    else:
                        self.ctrl.setPosition(Vec3(pt.x, pt.y, self.cruseAlt))
                        if self.ctrl.velCtrl.speed <= 0.00000001:
                            self.ctrl.sendEvent(self.ctrl.GO_EVT)
                        else:
                            self.ctrl.velCtrl.sendEvent(self.ctrl.velCtrl.IDLE_EVT)
                        self.ctrl.db(f"packages: {len(self.targetWaypoints)},")
                        #del(self.targetWaypoints[self.cargoIdx])
                else:
                    self.ctrl.db(f"======= TRYING TO DROP OFF =========== #{self.cargoIdx}")
            else:
                self.ctrl.db("Shutting down main rotor...")
                self.ctrl.altCtrl.sendEvent(self.ctrl.altCtrl.STOP_EVT)

    def getRemFuel(self):
        fuelPercent = 100.0
        fuel = base.myChoppers[self.id][1].remainingFuel_kg
        if self.fullTank is not None:
            fuelPercent = fuel / self.fullTank * 100.0
        self.ctrl.db(f"REMFUEL: {fuel:2.1f} kg ({fuelPercent:2.1f}%),")
        return fuel,fuelPercent