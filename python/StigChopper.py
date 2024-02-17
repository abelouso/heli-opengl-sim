#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode
from panda3d.core import CollisionTraverser, CollisionHandlerPusher
from direct.showbase.ShowBase import ShowBase

from BaseObject import *

class StigChopper(BaseObject):
    def __init__(self, id, pos, modelName, anims, colisName):
        BaseObject.__init__(self, pos, modelName,anims,colisName)
        
        base.pusher.addCollider(self.collider, self.actor)
        base.cTrav.addCollider(self.collider, base.pusher)

        #ported stuff
        self.size = Vec3(1,4,1.4)
        self.id = 0
        self.cargoCapacity = base.TOTAL_CAPACITY * 0.5
        self.inventory = int(self.cargoCapacity / base.ITEM_WEIGHT)

        self.m_fuelCapacity = base.TOTAL_CAPACITY * 0.5
        self.landed = True

        self.homeBase = None
        self.targetWaypoints = []
        self.id = id

    def setWaypoints(self, wp):
        self.targetWaypoints = wp
    
    def fuelCapacity(self):
        return self.m_fuelCapacity
    
    def itemCount(self):
        return self.inventory

    def getId(self):
        return self.id
    
    def deliverItem(self):
        ok = False
        if self.inventory:
            self.inventory -= 1
            ok = True
        return ok
    
    def getSize(self):
        return self.size

    def update(self,dt,tick):
        BaseObject.update(self,dt,tick)
        if base is not None:
            myPos = base.gps(self.id)
            if self.homeBase is None:
                self.homeBase = myPos
            self.actor.setPos(Vec3(myPos.x, myPos.y, myPos.z))
            rotation = base.transformations(self.id)
            self.actor.setHpr(rotation)

        self.runLogic(dt,tick)

    def runLogic(self,dt,tick):
        pass