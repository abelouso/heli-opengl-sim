#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode


import math
import queue
import time

from BaseObject import *
from StigChopper import *
from ApachiAlt import *

class Apachi(StigChopper):
    startTime = time.time_ns()
    def __init__(self,id, pos, scale=0.2):
        StigChopper.__init__(self,id,pos,"Models/ArmyCopter", {}, "apachi")
        self.actor.setScale(scale,scale,scale)
        self.rotDir = 1.0
        self.actAngle = 0
        self.mainSpeed = 0.0
        self.tilt = 0.0
        self.tailSpeed = 0.0
        self.altCtrl = ApachiAlt()
        self.altCtrl.trg = 70
        self.altCtrl.sendEvent(self.altCtrl.NULL_EVT)
        #self.m_fuelCapacity = 100

    def update(self,dt,tick):
        StigChopper.update(self,dt,tick)

    def runLogic(self,dt,tick):
        StigChopper.runLogic(self,dt,tick)
        pos = base.gps(self.id)
        alt = pos.getZ()
        self.tailSpeed = 100.0
        #TODO: provide access to this
        actSpd = base.myChoppers[self.id][1].actMainRotorSpeed_RPM
        self.mainSpeed = self.altCtrl.tick(alt,actSpd,dt)

        base.requestSettings(self.id,self.mainSpeed,self.tilt,self.tailSpeed)
        deltalNs = time.time_ns() - self.startTime
        TIME_IVAL = 35e9
        if self.altCtrl.state == self.altCtrl.AT_ALT_ST:
            if deltalNs > TIME_IVAL and self.altCtrl.trg == 70:
                self.altCtrl.setTarget(30)
            elif deltalNs > (2 * TIME_IVAL) and self.altCtrl.trg == 30:
                self.altCtrl.setTarget(0.3)




if __name__ == '__main__':
    print("Starting....")
    alt = AltHold()
    alt.sendEvent(alt.NULL_EVT)
    alt.tick(20,100)
    alt.tick(20,alt.rotorSpeed())