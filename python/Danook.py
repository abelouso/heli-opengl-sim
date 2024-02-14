#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode
import math

from BaseObject import *
from StigChopper import *

class Danook(StigChopper):
    def __init__(self,id, pos, scale=0.2):
        StigChopper.__init__(self,id,pos,"Models/Helicopter", {}, "danook")
        self.actor.setScale(scale,scale,scale)
        self.rotDir = 1.0
        self.actAngle = 0

    def update(self,dt,tick):
        StigChopper.update(self,dt,tick)
        self.actAngle += 1
        if (abs(self.actAngle) > 3600):
            self.rotDir *= -1.0
            self.actAngle = 0

        angDeg = tick * 6.0
        angRad = math.radians(angDeg)
        radius = 28 + 2.2 * self.id
        if True:
            pos = self.actor.getPos()
            pos.setX(radius * math.sin(angRad))
            pos.setY(-radius * math.cos(angRad))
            pos.setZ(79)
            self.actor.setPos(pos)
        else:
            self.actor.setPos(radius * math.cos(angRad), -radius * math.sin(angRad), 70)
        self.actor.setHpr(angDeg - 90.0,-5,-15)



    def runLogic(self,dt,tick):
        StigChopper.runLogic(self,dt,tick)