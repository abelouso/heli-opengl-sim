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
from Danook import *
from BaseObject import *
from StigChopper import *
from BuildingCluster import *
from ChopperInfo import *
from Camera import HeliCamera

gCH_ID = 0 #chopper index in chopper tuple
gIN_ID = 1 #info index in chopper tupple

class HeliMain(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        ##==================== PORTED STUFF ================
        ## from World.java
        self.CHOPPER_BASE_MASS = 100.0
        self.ITEM_WEIGHT = 10.0
        self.TOTAL_CAPACITY = 300.0

        self.TAG = "HeliMain"
        self.m_dbgMask = 0
        self.WORLD_DBG = 0x10000000
        self.nextChopperID = 0
        self.m_rtToRndRatio = 1.0
        self.sizeX = 10
        self.sizeY = 10
        self.sizeZ = 2
        self.curTimeStamp = 0.0
        
        self.TICK_TIME = 1.0 / 50.0
        self.FULL_BLOCK_SIZE = 100.0
        self.STREET_OFFSET = 3.0
        self.SIDEWALK_OFFSET = 2.0
        self.BLOCK_SIZE = self.FULL_BLOCK_SIZE - 2.0 * self.STREET_OFFSET
        self.SQUARE_SIZE = self.BLOCK_SIZE - 2.0 * self.SIDEWALK_OFFSET
        self.BUILDING_SPACE = (self.SQUARE_SIZE / 10.0)
        self.BUILDING_SIZE = 0.9 * self.BUILDING_SPACE
        self.HOUSES_PER_BLOCK = 10.0
        self.MAX_PACKAGE_DISTANCE = 2.0
        self.maxTime = 10000.0

        self.worldState = []
        self.allPackageLocs = []

        self.m_chopperInfoPanel = None

        ##==================================================
        
        self.pusher = CollisionHandlerPusher()
        self.cTrav = CollisionTraverser()

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

        self.myChoppers = {}
        id = 0
        danook = Danook(id,self.getStartingPosition(id))
        self.insertChopper(danook)
        
        id = 1
        apachi = Apachi(id,self.getStartingPosition(id))
        self.insertChopper(apachi)

        self.city = []
        self.generateCity()

        self.updateTask = taskMgr.add(self.update, "update")
        self.exitFunc = self.cleanup
        self.firstUpdate = True
        self.m_camToFollow = danook.id
        self.chaser = HeliCamera(self.cam.getX(),self.cam.getY(),self.cam.getZ())

    def cleanup(self):
        for chopper in self.myChoppers:
            self.myChoppers[chopper][gCH_ID].cleanUp()
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
        for chopper in self.myChoppers:
            self.myChoppers[chopper][gCH_ID].update(dt,task.time)
        
        if self.firstUpdate:
            self.cam.setPos(self.initialCameraPosition)
            self.cam.setHpr(0,-10,0)
            self.chaser.source = self.initialCameraPosition
            self.firstUpdate = False
        else:
            try:
                self.chaser.chase(self.myChoppers[self.m_camToFollow][gCH_ID].actor.getPos(),10)
                self.cam.setPos(self.chaser.source)
                self.cam.lookAt(self.myChoppers[self.m_camToFollow][gCH_ID].actor)
            except Exception as ex:
                print("Problem: ",ex)
            pass

        return task.cont

    '''
    World.java port here ===================================================================
    '''
    def dbg(self, tag, msg, bit):
        if self.m_dbgMask & bit:
            print("DEBUG: [",tag,"]:", msg)

    def getStartingPosition(self, chopperID):
        return Vec3(50.0, 48.0 + chopperID * 2.0, 0.0)
    
    def insertChopper(self, chopper):
        chInfo = ChopperInfo(chopper.id, chopper.fuelCapacity, chopper.actor.getPos(), 0.0)
        self.myChoppers[chopper.id] = (chopper,chInfo)

    def timeRatio(self):
        return self.m_rtToRndRatio

    def setChopperWaypoints(self):
        for key in self.myChoppers:
            chopper = self.myChoppers[key][gCH_ID]
            targetPoints = []
            for _ in range(0,chopper.itemCount()):
                whichRow = random.randint(0,20) - 10
                whichCol = random.randInt(0,20) - 10
                targetPoints.append(Vec3(whichCol, whichRow, 0.1))
            chopper.setWaypoints(targetPoints)
            self.allPackageLocs.append(targetPoints)

    def isAirborn(self,id):
        retVal = 1
        if id in self.myChoppers:
            if self.myChoppers[id][gCH_ID].onGround():
                retVal = 0
        return retVal

    def getFuelRemaining(self,id):
        retVal = 0
        if id in self.myChoppers:
            retVal = self.myChoppers[id][gIN_ID].getFuelRemaining()
        return retVal

    '''
    End of World.java port ======================================================================
    '''

heliMain = HeliMain()
heliMain.run()