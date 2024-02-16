#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode
import math

from BaseObject import *
from StigChopper import *

class Apachi(StigChopper):
    def __init__(self,id, pos, scale=0.2):
        StigChopper.__init__(self,id,pos,"Models/ArmyCopter", {}, "apachi")
        self.actor.setScale(scale,scale,scale)
        self.rotDir = 1.0
        self.actAngle = 0
        self.mainSpped = 0.0
        self.tilt = 0.0
        self.tailSpeed = 0.0

    def update(self,dt,tick):
        StigChopper.update(self,dt,tick)

        '''
        self.actAngle += 1
        if (abs(self.actAngle) > 3600):
            self.rotDir *= -1.0
            self.actAngle = 0

        angDeg = tick * 9.0
        angRad = math.radians(angDeg)
        radius = 39 + 2.2 * self.id
        if True:
            self.actor.setPos(radius * math.sin(angRad), -radius * math.cos(angRad), 70)
        else:
            self.actor.setPos(radius * math.cos(angRad), -radius * math.sin(angRad), 70)
        self.actor.setHpr(angDeg - 90.0,-5,-15)
        '''


    def runLogic(self,dt,tick):
        StigChopper.runLogic(self,dt,tick)
        pos = base.gps(self.id)
        alt = pos.getZ()
        if alt < 70:
            self.mainSpped = 100.0
            self.tailSpeed = 100.0
            self.tilt = 1
        elif alt < 10:
            self.mainSpeed = 70.0
        else:
            self.mainSpped -= 1.0
            self.tailSpeed = 0
            self.tilt = 0

        base.requestSettings(self.id,self.mainSpped,self.tilt,self.tailSpeed)
