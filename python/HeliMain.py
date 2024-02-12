#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight
from panda3d.core import Vec4, Vec3
from panda3d.core import CardMaker

#generic python
import random


#our imports
from Apachi import *
from BaseObject import *
from StigChopper import *
from BuildingCluster import *
from Camera import HeliCamera


class HeliMain(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.initialCameraPosition = Vec3(0,-340, -60)
        ambientLight = AmbientLight("ambient light")
        ambientLight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        self.ambientLightNodePath = render.attachNewNode(ambientLight)
        render.setLight(self.ambientLightNodePath)
        render.setShaderAuto()

        mainLight = DirectionalLight("main light")
        self.mainLightNodePath = render.attachNewNode(mainLight)
        # Turn it around by 45 degrees, and tilt it down by 45 degrees
        self.mainLightNodePath.setHpr(45, -45, 0)
        render.setLight(self.mainLightNodePath)
        
        cm = CardMaker("plane")
        planeSide = 700
        cm.setFrame(0, -planeSide, 0, planeSide) #set the size here
        plane=render.attachNewNode(cm.generate())
        plane.setHpr(0,90,0)
        plane.setPos(0.5 * planeSide, 0.5 * planeSide,0)

        self.choppers = []
        self.choppers.append(Apachi())

        self.city = []
        self.generateCity()

        self.updateTask = taskMgr.add(self.update, "update")
        self.exitFunc = self.cleanup
        self.firstUpdate = True
        self.followIndex = len(self.choppers) - 1
        self.chaser = HeliCamera(self.cam.getX(),self.cam.getY(),self.cam.getZ())

    def cleanup(self):
        for chopper in self.choppers:
            chopper.cleanUp()
        for bld in self.city:
            bld.cleanUp()
        
    def quit(self):
        self.cleanup()
        base.userExit()

    def generateCityBlock(self,numBldgs, gridX, gridY):

        bldType = random.randint(1,5)
        stepX = 30
        stepY = stepX
        offsetX = gridX - 0.5 * numBldgs * stepX
        offsetY = gridY - 0.5 * numBldgs * stepY
        for xIdx in range(0,numBldgs):
            for yIdx in range(0,numBldgs):
                toPlace = random.randint(0,1)
                if toPlace == 1:
                    pos = Vec3(offsetX + xIdx * stepX, offsetY + yIdx * stepY,0)
                    self.city.append(BuildingCluster(bldType,pos))

    def generateCity(self):
        cityX = 50
        cityY = 50
        blockX = 5
        blockY = 5
        for gridX in range(-cityX,cityX,blockX):
            for gridY in range(-cityY,cityY,blockY):
                self.generateCityBlock(numBldgs=1,gridX = blockX * gridX, gridY=blockY *gridY)
    
    def update(self,task):
        dt = globalClock.getDt()
        for chopper in self.choppers:
            chopper.update(dt,task.time)
        
        if self.firstUpdate:
            print(" ================= setting camera position ================")
            self.cam.setPos(self.initialCameraPosition)
            self.cam.setHpr(0,-10,0)
            self.chaser.source = self.initialCameraPosition
            self.firstUpdate = False
        else:
            try:
                self.chaser.chase(self.choppers[self.followIndex].actor.getPos(),10)
                self.cam.setPos(self.chaser.source)
                #self.cam.setPos(self.choppers[self.followIndex].actor.getPos() + 10)
                #self.cam.setHpr(self.chaser.getHpr())
                self.cam.lookAt(self.choppers[self.followIndex].actor)
                #base.camera.lookAt(self.camera, self.choppers[self.followIndex].actor,up=Vec3(0,1,0))
            except Exception as ex:
                print("Problem: ",ex)
            pass

        return task.cont

heliMain = HeliMain()
heliMain.run()