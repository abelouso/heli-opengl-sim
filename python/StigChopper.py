#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode
from panda3d.core import CollisionTraverser, CollisionHandlerPusher
from direct.showbase.ShowBase import ShowBase

from BaseObject import *
import random

class StigChopper(BaseObject):
    def __init__(self, id, pos, modelName, anims, colisName):
        BaseObject.__init__(self, pos, modelName,anims,colisName)
        
        '''
        self.RotorPath = None
        if len(self.actor.children) > 0:
            print(f"List is not empty!")
        else:
            print(f"List is empty")
        for child in self.actor.children:
            print(f"Model: {modelName}, Joint: {child.name}")
            self.rotorPath = child.find("Rotor")
            if not self.rotorPath is None:
                print(f"Found rotor")
        '''

        base.pusher.addCollider(self.collider, self.actor)
        base.cTrav.addCollider(self.collider, base.pusher)

        #constants
        self.VERT_OFFSET = 1.0
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

    def update(self,currentTime,elapsedTime):
        BaseObject.update(self,currentTime,elapsedTime)
        if base is not None:
            myPos = base.gps(self.id)
            if self.homeBase is None:
                self.homeBase = myPos
            '''
            if not self.rotorPath is None:
                self.rotorPath.setHpr(random.randint(0,359),0.0, 0.0)
            '''
            self.actor.setPos(Vec3(myPos.x, myPos.y, myPos.z + self.VERT_OFFSET))
            rotation = base.transformations(self.id)
            self.actor.setHpr(Vec3(rotation.x - 90.0,rotation.y, rotation.z))

        self.runLogic(currentTime,elapsedTime)

    def runLogic(self,dt,tick):
        pass