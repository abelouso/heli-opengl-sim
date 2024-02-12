#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode


class BaseObject():
    def __init__(self, pos, modelName, anims, colliderName):
        self.actor = Actor(modelName, anims)
        self.actor.reparentTo(render)
        self.actor.setPos(pos)
        # Note the "colliderName"--this will be used for
        # collision-events, later...
        colliderNode = CollisionNode(colliderName)
        ##TODO: update colision box for this object
        colliderNode.addSolid(CollisionSphere(0, 0, 0, 0.3))
        self.collider = self.actor.attachNewNode(colliderNode)
        # See below for an explanation of this!
        self.collider.setPythonTag("owner", self)

    def update(self,dt,tick):
        pass

    def cleanUp(self):
        # Remove various nodes, and clear the Python-tag--see below!

        if self.collider is not None and not self.collider.isEmpty():
            try:
                self.collider.clearPythonTag("owner")
                base.cTrav.removeCollider(self.collider)
                base.pusher.removeCollider(self.collider)
            except:
                pass

        if self.actor is not None:
            self.actor.cleanup()
            self.actor.removeNode()
            self.actor = None

        self.collider = None