#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
import random
import math

gMinDefault = 1.4

class HeliCamera:
    def __init__(self, trgX = 0, trgY = 0, trgZ = 0):
        self.orbitAltitude = 20.0
        self.orbitRadius = trgX
        self.source = Vec3(trgX,(-trgY/2),self.orbitAltitude)
        self.target = Vec3(trgX, trgY, trgZ)
        self.upUnit = Vec3(0.0,1.0,0.0)
        self.fovDegrees = 60.0
        self.nearClip = 5.0
        self.farClip = 1500.0
        self.curAngle = 0
        self.sceneWidth = 100
        self.sceneHeight = 100

    def setTarget(self, inPoint):
        self.target = inPoint

    def wobble(self):
        deltaX = 2 * random.randint(0,100) * 0.02 - 1
        deltaY = 2 * random.randint(0,100) * 0.02 - 1
        deltaZ = 2 * random.randint(0,100) * 0.02 - 1
        self.source = Vec3(self.source.getX() + deltaX, 
                           self.source.getY() + deltaY, 
                           self.source.getZ() + deltaZ)
        
    def approach(self,approachPercent):
        appr = (approachPercent / 100)
        deltaD = (self.source - self.target)
        deltaD = Vec3(deltaD.getX() * appr, deltaD.getY() * appr, deltaD.getZ() * appr)
        dist = deltaD.length()
        self.source = self.source - deltaD

    def chase(self, newTarget, minDistance = gMinDefault):
        if minDistance < self.nearClip:
            minDistance = self.nearClip

        oTrg = self.target
        oSrc = self.source
        self.target = newTarget
        above = 3

        if self.source.getZ() < (self.target.getZ() + above):
            self.source.setZ(self.target.getZ() + above)
        
        actDistance = (self.source - self.target).length()

        if actDistance > (minDistance * 1.04):
            self.approach(0.25 * (actDistance / minDistance))

    def orbit(self, ticksPerRev):
        if ticksPerRev < 60:
            ticksPerRev = 60
        self.curAngle = math.pi / ticksPerRev
        dX = self.orbitRadius * math.sin(self.curAngle)
        dY = self.orbitRadius * math.cos(self.curAngle)
        self.source = Vec3(self.target.getX() + dX,
                            self.target.getY() + dY,
                            self.target.getZ() + self.orbitAltitude)
        
    def getHpr(self):
        x2 = self.target.getX()
        y2 = self.target.getY()
        z2 = self.target.getZ()
        
        x1 = self.source.getX()
        y1 = self.source.getY()
        z1 = self.source.getZ()


        # Calculate yaw angle
        yaw = math.atan2(x2 - x1, y2 - y1)

        # Calculate pitch angle
        pitch = math.atan2(y2 - y1, x2 - x1)

        # Calculate roll angle
        roll = math.atan2(z2 - z1, math.hypot(x2 - x1, y2 - y1))

        print("yaw: ",yaw, ",pitch: ",pitch, ",roll: ",roll)

        res = Vec3(math.degrees(yaw),
                   math.degrees(pitch), #panda HeliCamera is looking at +Y
                   math.degrees(roll))

        return res


if __name__ == "__main__":
    camFlow = HeliCamera()
    camFlow.setTarget(Vec3(12,33,11))
    camFlow.approach(20)
    print(camFlow.source)
    camFlow.wobble()
    print(camFlow.source)
    camFlow.chase(Vec3(22,33,11))
    print(camFlow.source)
    camFlow.chase(Vec3(32,30, 10))
    print(camFlow.source)
    camFlow.orbit(30)
    print(camFlow.source)
    camFlow.source = Vec3(0,0,0)
    camFlow.target = Vec3(300,300,1)
    print(camFlow.getHpr())