#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode
import math

from BaseObject import *
from StigChopper import *


class BuildingCluster(BaseObject):
    def __init__(self,clID,pos,scale=0.35):
        BaseObject.__init__(self,pos,f"Models/BuildingCluster{clID}", {}, f"bldClst")
        self.actor.setScale(scale,scale,scale)
        self.actor.setPos(pos)
        self.actor.setHpr(0,0,0)