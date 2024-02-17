#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode
import math
from enum import Enum

from BaseObject import *
from StigChopper import *

class State(Enum):
    LANDED = 0,
    STOP_NOW = 1,
    FINDING_HEADING = 2,
    APPROACHING = 3

class Danook(StigChopper):
    def __init__(self,id, pos, scale=0.2):
        StigChopper.__init__(self,id,pos,"Models/Helicopter", {}, "danook")
        self.actor.setScale(scale,scale,scale)
        self.rotDir = 1.0
        self.actAngle = 0
        # constants
        self.VERT_CONTROL_FACTOR = 2.5
        self.HORZ_CONTROL_FACTOR = 0.15
        self.MAX_VERT_VELOCITY = 2.5
        self.MAX_HORZ_VELOCITY = 2.5
        self.MAX_VERT_ACCEL = 0.4
        self.MAX_HORZ_ACCEL = 0.4
        self.DECEL_DISTANCE_VERT = 12.0
        self.DECEL_DISTANCE_HORZ = 16.0
        self.VERT_DECEL_SPEED = 0.5
        self.HORZ_DECEL_SPEED = 2.0
        self.MAX_FAIL_COUNT = 40
        self.TAG = "Danook"
        self.DEBUG_BIT = 0x8000

        # Control factors ported from Danook Controller
        self.myState = State(State.LANDED)
        self.desMainRotorSpeed_RPM = 0.0
        self.desTailRotorSpeed_RPM = 0.0
        self.desTilt_Degrees = 0.0
        self.estimatedAcceleration = None
        self.estimatedVelocity = None
        self.lastPosition = None
        self.actualPosition = pos
        self.currentDestination = None
        self.lastTime = 0.0
        self.currTime = 0.0

    def __findClosestDestination(self) -> Vec3:
        resultPoint = None
        minDistance = 10000.0
        for testPoint in self.targetWaypoints:
            deltaX = testPoint.x - self.actualPosition.x
            deltaY = testPoint.y - self.actualPosition.y
            curDistance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
            if curDistance < minDistance:
                resultPoint = testPoint
                minDistance = curDistance
        return resultPoint

    def __adjustHeading(self, useVelocity) -> bool:
        headingOK = False
        if self.currentDestination is None:
            return headingOK
        transformation = base.transformations(self.getId())
        if transformation is None:
            return headingOK
        actHeading = transformation.x
        deltaY = self.currentDestination.y - self.actualPosition.y
        deltaX = self.currentDestination.x - self.actualPosition.x
        if useVelocity:
            deltaY = self.estimatedVelocity.y
            deltaX = self.estimatedVelocity.x
        desiredHeading = math.degrees(math.atan2(deltaX, deltaY))
        if desiredHeading < 0.0:
            desiredHeading += 360.0
        deltaHeading = desiredHeading - actHeading
        if deltaHeading < -180.0:
            deltaHeading += 360.0
        elif deltaHeading > 180.0:
            deltaHeading -= 360.0
        if abs(deltaHeading < 0.05):
            self.desTailRotorSpeed_RPM = 100.0
            base.requestSettings(self.getId(), self.desMainRotorSpeed_RPM, self.desTilt_Degrees, self.desTailRotorSpeed_RPM)
            headingOK = True
        else:
            deltaRotor = (deltaHeading / 10.0) * 20.0
            if deltaRotor > 5.0:
                deltaRotor = 5.0
            elif deltaRotor < -5.0:
                deltaRotor = -5.0
            self.desTailRotorSpeed_RPM = 100.0 + deltaRotor
            base.requestSettings(self.getId(), self.desMainRotorSpeed_RPM, self.desTilt_Degrees, self.desTailRotorSpeed_RPM)
        return headingOK

    def __estimateVelocity(self, deltaTime) -> Vec3:
        deltaX = self.lastPosition.x - self.actualPosition.x
        deltaY = self.lastPosition.y - self.actualPosition.y
        oldVelocity = self.estimatedVelocity
        self.estimatedVelocity = Vec3((self.actualPosition.x - self.lastPosition.x) / deltaTime, (self.actualPosition.y - self.lastPosition.x) / deltaTime, (self.actualPosition.z - self.lastPosition.x) / deltaTime)
        return oldVelocity

    def __estimateAcceleration(self, lastVelocity, deltaTime) -> Vec3:
        oldAcceleration = self.estimatedAcceleration
        self.estimatedAcceleration = Vec3((self.estimatedVelocity.x - lastVelocity.x) / deltaTime, (self.estimatedVelocity.y - lastVelocity.x) / deltaTime, (self.estimatedVelocity.z - lastVelocity.x) / deltaTime)
        return oldAcceleration

    def __estimatePhysics(self) -> bool:
        updated = False
        deltaTime = self.currTime - self.lastTime
        if deltaTime < 0.001:
            return updated
        updated = True
        base.dbg(self.TAG, "Estimating Physics", self.DEBUG_BIT)
        oldVelocity = self.__estimateVelocity(deltaTime)
        if (not oldVelocity is None):
            oldAcceleration = self.__estimateAcceleration(oldVelocity, deltaTime)
        return updated

    # returns numeric (double) type
    def __computeDesiredAcceleration(self,actVel, desVel, doVertical):
        targetAccel = self.MAX_VERT_ACCEL if doVertical else self.MAX_HORZ_ACCEL
        deltaValue = abs(desVel - actVel)
        DECEL_SPEED = self.VERT_DECEL_SPEED if doVertical else self.HORZ_DECEL_SPEED
        if deltaValue < DECEL_SPEED:
            targetAccel = deltaValue / DECEL_SPEED
        if actVel > desVel:
            targetAccel *= -1.0
        return targetAccel

    # returns numeric (double) type
    def __computeDesiredVelocity(self,actAlt, desAlt, doVertical):
        targetVelocity = self.MAX_VERT_VELOCITY if doVertical else self.MAX_HORZ_VELOCITY
        deltaValue = abs(desAlt - actAlt)
        DECEL_DISTANCE = self.DECEL_DISTANCE_VERT if doVertical else self.DECEL_DISTANCE_HORZ
        if deltaValue < DECEL_DISTANCE:
            targetVelocity = deltaValue / DECEL_DISTANCE
        if actAlt > desAlt:
            targetVelocity *= -1.0
        return targetVelocity

    def __approachTarget(self, justStop) -> bool:
        success = False
        if self.currentDestination is None and justStop == False:
            return False
        deltaVector = Vec3(0.0, 0.0, 0.0)
        if justStop == False:
            deltaX = self.currentDestination.x - self.actualPosition.x
            deltaY = self.currentDestination.y - self.actualPosition.y
            deltaVector = Vec3(deltaX, deltaY, 0.0)
        actualDestination = self.currentDestination
        if justStop:
            actualDestination = self.actualPosition
        targetXVelocity = 0.0
        if justStop == False:
            targetXVelocity = self.__computeDesiredVelocity(self, self.actualPosition.x, self.currentDestination.x, False)
        targetXAcceleration = self.__computeDesiredAcceleration(self, self.estimatedVelocity.x, targetXVelocity, False)
        xMultiplier = 1.0
        deltaXAcceleration = targetXAcceleration - self.estimatedAcceleration.x
        if deltaXAcceleration > self.MAX_HORZ_ACCEL:
            xMultiplier = self.MAX_HORZ_ACCEL / deltaXAcceleration
        if deltaXAcceleration < -self.MAX_HORZ_ACCEL:
            xMultiplier = (-self.MAX_HORZ_ACCEL) / deltaXAcceleration
        # repeat for Y
        targetYVelocity = 0.0
        if justStop == False:
            targetYVelocity = self.__computeDesiredVelocity(self, self.actualPosition.y, self.currentDestination.y, False)
        targetYAcceleration = self.__computeDesiredAcceleration(self, self.estimatedVelocity.y, targetYVelocity, False)
        yMultiplier = 1.0
        deltaYAcceleration = targetYAcceleration - self.estimatedAcceleration.y
        if deltaYAcceleration > self.MAX_HORZ_ACCEL:
            yMultiplier = self.MAX_HORZ_ACCEL / deltaYAcceleration
        if deltaYAcceleration < -self.MAX_HORZ_ACCEL:
            yMultiplier = (-self.MAX_HORZ_ACCEL) / deltaYAcceleration

        # Limit size of the vector but do not change the proportion
        if xMultiplier < yMultiplier:
            deltaXAcceleration *= yMultiplier
            deltaYAcceleration *= yMultiplier
        else:
            deltaXAcceleration *= xMultiplier
            deltaYAcceleration *= xMultiplier
        deltaAcceleration = math.sqrt(deltaXAcceleration * deltaXAcceleration + deltaYAcceleration * deltaYAcceleration)
        accelHeading = math.degrees(math.atan2(deltaXAcceleration, deltaYAcceleration))
        moveHeading = math.degrees(math.atan2(deltaVector.x, deltaVector.y))
        deltaAngle = abs(accelHeading - moveHeading)
        if deltaAngle > 90:
            deltaAcceleration *= -1.0
        self.desTilt_Degrees += deltaAcceleration * self.HORZ_CONTROL_FACTOR
        if justStop:
            base.dbg(self.TAG, "Trying to stop...", self.DEBUG_BIT)
            if self.estimatedVelocity.xyLength() < 0.1:
                success = True
        else:
            success = True
        return success
        
    def __selectDesiredAltitude(self):
        self.desiredAltitude = 0.0
        if not self.currentDestination is None:
            deltaX = self.currentDestination.x - self.actualPosition.x
            deltaY = self.currentDestination.y - self.actualPosition.y
            distance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
            if distance > 5.0:
                self.desiredAltitude = 110.0
        else:
            base.dbg(self.TAG, "No destination yet", self.DEBUG_BIT)

    def __controlAltitude(self, inState) -> State:
        base.dbg(self.TAG, "In control altitude...", self.DEBUG_BIT)
        outState = inState
        if self.estimatedVelocity is None or self.estimatedAcceleration is None:
            return outState
        base.dbg(self.TAG, "Proceeding to ground check", self.DEBUG_BIT)
        #flightState = base.isAirborn(self.getId())
        flightState = self.actualPosition.getZ() > 0.0
        onGround = flightState == 0
        if onGround:
            base.dbg(self.TAG, "On the ground...", self.DEBUG_BIT)
            if not self.currentDestination is None:
                deltaX = self.currentDestination.x - self.actualPosition.x
                deltaY = self.currentDestination.y - self.actualPosition.y
                actDistance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
                if (actDistance < base.MAX_PACKAGE_DISTANCE):
                    base.dbg(self.TAG, "Try to deliver...", self.DEBUG_BIT)
                    delivered = base.deliverPackage(self.getId())
                    if delivered:
                        #TODO: Delete waypoint if world didn't
                        base.dbg(self.TAG, "Delivered a package", self.DEBUG_BIT)
                    else:
                        base.dbg(self.TAG, "Couldn't deliver package (why?)" , self.DEBUG_BIT)
                else:
                    base.dbg(self.TAG, "Too far to deliver package", self.DEBUG_BIT)
                outState = State.FINDING_HEADING
            else:
                base.dbg(self.TAG, "Landed with no destination?", self.DEBUG_BIT)
            base.dbg(self.TAG,"done with ground stuff", self.DEBUG_BIT)
            if inState == State.APPROACHING:
                outState = State.LANDED
            return outState
        else:
            base.dbg(self.TAG, "Something else", self.DEBUG_BIT)
            if inState == State.LANDED:
                outState = State.FINDING_HEADING
        targetVertVelocity = self.__computeDesiredVelocity(self.actualPosition.z, self.desiredAltitude, True)
        targetVertAcceleration = self.__computeDesiredAcceleration(self.estimatedVelocity.z - targetVertVelocity, True)
        deltaAcceleration = targetVertAcceleration - self.estimatedAcceleration.z
        if deltaAcceleration > self.MAX_VERT_ACCEL:
            deltaAcceleration = self.MAX_VERT_ACCEL
        if deltaAcceleration < (-self.MAX_VERT_ACCEL):
            deltaAcceleration = -self.MAX_VERT_ACCEL
        self.desMainRotorSpeed_RPM += deltaAcceleration * self.VERT_CONTROL_FACTOR
        base.dbg(self.TAG, "Desired main rotor: " + str(desMainRotorSpeed_RPM) + ", tail rotor: " + str(desTailRotorSpeed_RPM),self.DEBUG_BIT)
        base.request_settings(self.desMainRotorSpeed_RPM, self.desTilt_Degrees, self.desTailRotorSpeed_RPM)
        return outState
        
    def __controlTheShip(self, isCloser):
        base.dbg(self.TAG, "Control the ship -- state: " + str(self.myState), self.DEBUG_BIT)
        if self.myState == State.APPROACHING and isCloser == False:
            self.myState = State.STOP_NOW
        nextState = self.myState
        match self.myState:
            case State.LANDED:
                base.dbg(self.TAG, "No Action Needed", self.DEBUG_BIT)
            case State.STOP_NOW:
                # stop spinning
                self.desTailRotorSpeed_RPM = 100.0 # Stable
                success = self.__approachTarget(True)
                if success:
                    nextState = State.FINDING_HEADING
            case State.FINDING_HEADING:
                headingOK = self.__adjustHeading(False)
                if headingOK:
                    nextState = State.APPROACHING
            case State.APPROACHING:
                self.__approachTarget(False)
            case _:
                base.dbg(self.TAG, "Unexpected State", self.DEBUG_BIT)
                raise RuntimeError
        self.myState = nextState
        self.__selectDesiredAltitude()
        #try:
        self.myState = self.__controlAltitude(self.myState)
        #except:
            #base.dbg(self.TAG, "Exception in altitude control", self.DEBUG_BIT)

    def update(self,dt,tick):
        StigChopper.update(self,dt,tick)
        '''
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
            pos.setZ(0)
            self.actor.setPos(self.actualPosition)
        else:
            self.actor.setPos(radius * math.cos(angRad), -radius * math.sin(angRad), 70)
        self.actor.setHpr(angDeg - 90.0,-5,-15)
        '''

    def runLogic(self,dt,tick):
        StigChopper.runLogic(self,dt,tick)
        self.lastPosition = self.actualPosition
        self.actualPosition = base.gps(self.getId())
        self.currTime = tick
        base.dbg(self.TAG, "Current Tick: " + str(self.currTime), self.DEBUG_BIT)
        if self.currentDestination is None:
            self.currentDestination = self.__findClosestDestination()
            if not self.currentDestination is None:
                base.dbg(self.TAG, "Got a destination", self.DEBUG_BIT)
        if (not self.lastPosition is None and self.lastTime < self.currTime):
            updated = self.__estimatePhysics()
            if updated:
                closer = True
                if not self.currentDestination is None:
                    deltaX = self.currentDestination.x - self.lastPosition.x
                    deltaY = self.currentDestination.y - self.lastPosition.y
                    oldDistance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
                    deltaX = self.currentDestination.x - self.actualPosition.x
                    deltaY = self.currentDestination.y - self.actualPosition.y
                    newDistance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
                    if newDistance > (oldDistance + 0.5):
                        closer = False
                        base.dbg(self.TAG, "Wrong way now: " + newDistance + " then: " + oldDistance, self.DEBUG_BIT)
                self.__controlTheShip(closer)
            else:
                base.dbg(self.TAG, "No physics estimate?", self.DEBUG_BIT)
        self.lastTime = self.currTime