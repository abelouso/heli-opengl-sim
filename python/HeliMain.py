#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight
from panda3d.core import Vec4, Vec3
from panda3d.core import CardMaker
from panda3d.core import loadPrcFile
from panda3d.core import ExecutionEnvironment

#generic python
import random
import argparse
import math
import multiprocessing as mp

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
        self.sizeX = 50
        self.sizeY = 50
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
        self.MAX_PACKAGE_DISTANCE = 1.0
        self.maxTime = 10000.0

        self.worldState = []
        self.allPackageLocs = {}

        self.m_chopperInfoPanel = None
        self.m_camToFollow = 1

        ap = argparse.ArgumentParser(description="Helicopter Delivery World Simulator")
        ap.add_argument("-x",help="World's x size",default = self.sizeX,dest="sizeX")
        ap.add_argument("-y",help="World's y size",default = self.sizeY,dest="sizeY")
        ap.add_argument("-z",help="World's z size",default = self.sizeZ,dest="sizeZ")
        ap.add_argument("-d",help="Debug mask",default="0",dest="debugMask")
        ap.add_argument("-c",help="Index of a chopper to follow",dest="camToFollow",default=0)
        ap.add_argument("-f",help="ratio of world to real time 1 - for real-time 10 - 10x faster",default=self.m_rtToRndRatio,dest="rtRatio")

        args = ap.parse_args()
        self.sizeX = int(args.sizeX)
        self.sizeY = int(args.sizeY)
        self.sizeZ = int(args.sizeZ)
        self.m_dbgMask = int(args.debugMask,0)
        self.m_rtToRndRatio = float(args.rtRatio)
        self.m_camToFollow = float(args.camToFollow)

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

        self.city = []
        self.landings = []
        self.generateCity()

        self.myChoppers = {}
        id = 0
        danook = Danook(id,self.getStartingPosition(id))
        self.insertChopper(danook)
        
        id = 1
        apachi = Apachi(id,self.getStartingPosition(id))
        self.insertChopper(apachi)

        self.updateTask = taskMgr.add(self.update, "update")
        self.exitFunc = self.cleanup
        self.firstUpdate = True
        self.chaser = HeliCamera(self.cam.getX(),self.cam.getY(),self.cam.getZ())
        self.setChopperWaypoints()
        for landing in self.landings:
            # -1 just means don't give it a color
            self.addLandingPad(-1, landing)

    def cleanup(self):
        for chopper in self.myChoppers:
            self.myChoppers[chopper][gCH_ID].cleanUp()
        for bld in self.city:
            bld.cleanUp()
        
    def quit(self):
        self.cleanup()
        base.userExit()

    def generateCityBlock(self,numBldgs, gridX, gridY):
        bldType = random.randint(1,4)
        stepX = 30
        stepY = stepX
        offsetX = gridX - 0.5 * numBldgs * stepX
        offsetY = gridY - 0.5 * numBldgs * stepY
        for xIdx in range(0,numBldgs):
            for yIdx in range(0,numBldgs):
                toPlace = random.randint(0,1)
                centerX = offsetX + xIdx * stepX
                centerY = offsetY + yIdx * stepY
                pos = Vec3(centerX, centerY,0)
                if toPlace == 1:
                    self.city.append(BuildingCluster(bldType,pos))
                else:
                    self.landings.append(pos)

    def generateCity(self):
        cityX = self.sizeX
        cityY = self.sizeY
        blockX = 5
        blockY = 5
        for gridX in range(-cityX,cityX,blockX):
            for gridY in range(-cityY,cityY,blockY):
                self.generateCityBlock(numBldgs=1,gridX = blockX * gridX, gridY=blockY *gridY)
    
    def addLandingPad(self, id, pos):
        colorRed   = 1.0
        colorGreen = 1.0
        colorBlue  = 1.0
        colorAlpha = 1.0
        if id == 0:
            colorRed = 0.0
            colorGreen = 0.0
        elif id == 1:
            colorGreen = 0.0
            colorBlue = 0.0
        imageObject = OnscreenImage(image="resource/helipad_256.png", pos=(pos.x, pos.y, 0.05), scale=2.0, color=(colorRed, colorGreen, colorBlue, colorAlpha))
        imageObject.setHpr(0, -90, 0)
        imageObject.reparentTo(render)

    def update(self,task):
        dt = globalClock.getDt()
        self.tick(dt)
        for chopper in self.myChoppers:
            
            self.myChoppers[chopper][gCH_ID].update(self.curTimeStamp,self.TICK_TIME)
            '''
            try:
                self.myChoppers[chopper][gCH_ID].update(self.curTimeStamp,self.TICK_TIME)
            except Exception as ex:
                self.dbg(self.TAG, f"ERROR in update(): exception with id {chopper}: {ex}",self.WORLD_DBG)
            '''
        self.curTimeStamp += self.TICK_TIME
        
        if self.firstUpdate:
            self.cam.setPos(self.initialCameraPosition)
            self.cam.setHpr(0,-10,0)
            self.chaser.source = self.initialCameraPosition
            self.firstUpdate = False
        else:
            try:
                self.chaser.chase(self.myChoppers[self.m_camToFollow][gCH_ID].actor.getPos(),20)
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
            print("DEBUG: [",tag,"]:", msg, flush=True)

    def getStartingPosition(self, chopperID):
        whichPos = random.randint(0, len(self.landings)-1)
        landing = self.landings[whichPos]
        self.addLandingPad(chopperID, landing)
        del(self.landings[whichPos])
        return landing
    
    def insertChopper(self, chopper):
        chInfo = ChopperInfo(chopper.id, chopper.fuelCapacity(), chopper.actor.getPos(), 0.0)
        self.myChoppers[chopper.id] = (chopper,chInfo)

    def timeRatio(self):
        return self.m_rtToRndRatio

    def setChopperWaypoints(self):
        for key in self.myChoppers:
            chopper = self.myChoppers[key][gCH_ID]
            targetPoints = []
            for idx in range(0,chopper.itemCount()):
                whichPos = random.randint(0, len(self.landings)-1)
                targetPoints.append(self.landings[whichPos])
                del(self.landings[whichPos])
            self.dbg(self.TAG, "Chopper {} given waypoints -- {} points left".format(key, len(self.landings)), self.WORLD_DBG)
            chopper.setWaypoints(targetPoints)
            self.allPackageLocs[key] = targetPoints

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
    
    def deliverPackage(self, id):
        self.dbg(self.TAG,"Chopper " + str(id) + " trying to deliver a package", self.WORLD_DBG)
        success = False
        if id in self.myChoppers:
            chop,info = self.myChoppers[id]
            myPos = self.gps(id)
            if info.onGround():
                self.dbg(self.TAG,"Chopper " + str(id) + " confirmed on ground", self.WORLD_DBG)
				## OK, check position
				## NOTE: I believe the hashCode function is used to determine
				## if the container has the object.  That only includes X,Y,Z
				## which is what I think we want.
                object = self.allPackageLocs[id]
                for avec3 in object:
                    deltaX = avec3.x - myPos.x
                    deltaY = avec3.y - myPos.y
                    delta = math.sqrt(deltaX * deltaX + deltaY * deltaY)
                    self.dbg(self.TAG,f"Checking: vec {avec3.x:3.4f},{avec3.y:3.4f},{avec3.z:3.4f}, dist: {delta: 3.4f}, id: {id}",self.WORLD_DBG)
                    if delta < self.MAX_PACKAGE_DISTANCE:
                        self.dbg(self.TAG,"Chopper {} delivered package to ({:.2f}, {:.2f})".format(id, avec3.x, avec3.y), self.WORLD_DBG)
                        object.remove(avec3)
                        # Key to remove the waypoint from the chopper's list
                        # Otherwise it could try again at the same location
                        chop.setWaypoints(object)
                        success = True
                        break
                if not success:
                    self.dbg(self.TAG,f"Couldn't find package to deliver at ({myPos})", self.WORLD_DBG)
        return success

    def getChopper(self,id):
        if id in self.myChoppers:
            return self.myChoppers[id][gCH_ID]
        else:
            return None

    def getTimestamp(self):
        return self.curTimeStamp

    def requestSettings(self, id, mainRotorSpeed, tiltAngle, tailRotorSpeed):
        if id in self.myChoppers:
            _ , resInfo = self.myChoppers[id]
            resInfo.requestMainRotorSpeed(mainRotorSpeed)
            resInfo.requestTailRotorSpeed(tailRotorSpeed)
            resInfo.requestTiltLevel(tiltAngle)

    def requestNextChopperID(self):
        getNext = False
        for id in self.myChoppers:
            if getNext:
                self.nextChopperID = id
                break
            if id == self.nextChopperID:
                getNext = True

    # I think dt is deprecated unless we want to pass self.TICK_TIME to it
    def tick(self, dt):
        outOfTime = False
        for id in self.myChoppers:
            try:
                self.myChoppers[id][gIN_ID].fly(self.curTimeStamp, self.TICK_TIME)
            except Exception as ex:
                self.dbg(self.TAG, f"ERROR in tick(): exception with id {id}: {ex}",self.WORLD_DBG)
        return outOfTime
               
    def gps(self,id):
        if id in self.myChoppers:
            return self.myChoppers[id][gIN_ID].getPosition()
        else:
            return Vec3(0,0,0)
        
    def transformations(self,id):
        if id in self.myChoppers:
            info = self.myChoppers[id][gIN_ID]
            txfm = Vec3(info.getHeading(), -info.getTilt(), 0.0)
            return txfm
        else:
            return Vec3(0,0,0)
        
    '''
    End of World.java port ======================================================================
    '''

def main():
    # Any config must be loaded before ShowBase is instantiated in constructor
    root = ExecutionEnvironment.getCwd()
    fullPath = root + "/config/Config.prc"
    print("Trying to open config: " + str(fullPath))
    loadPrcFile(fullPath)
    heliMain = HeliMain()
    heliMain.run()

if __name__ == "__main__":
    mp.freeze_support()
    main()