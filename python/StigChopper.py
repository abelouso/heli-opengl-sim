#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode

from BaseObject import *


class StigChopper(BaseObject):
    def __init(self, pos, modelName, anims, colisName):
        BaseObject.__init__(self, pos, modelName,anims,colisName)
        
        base.pusher.addCollider(self.collider, self.actor)
        base.cTrav.addCollider(self.collider, base.pusher)

    def update(self,dt,tick):
        BaseObject.update(self,dt,tick)

        self.runLogic(dt,tick)

    def runLogic(self,dt,tick):
        pass