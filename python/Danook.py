#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec4, Vec3, Vec2
from direct.actor.Actor import Actor
from panda3d.core import CollisionSphere, CollisionNode
import math
import time
from enum import Enum

from BaseObject import *
from StigChopper import *

class State(Enum):
    LANDED = 0,
    CLIMB = 1,
    FINDING_HEADING = 2,
    STABILIZE_ROTATION = 3,
    APPROACHING = 4,
    STOP_NOW = 5,
    TASKS_COMPLETE = 6,
    POWER_DOWN = 7

class Danook(StigChopper):
    def __init__(self,id, pos, scale=0.2):
        StigChopper.__init__(self,id,pos,"Models/Helicopter", {}, "danook")
        self.actor.setScale(scale,scale,scale)
        self.rotDir = 1.0
        self.actAngle = 0
        # constants
        self.VERT_CONTROL_FACTOR   = 2.9   # original 2.5
        self.HORZ_CONTROL_FACTOR   = 0.14  # original 0.15
        self.MAX_VERT_VELOCITY     = 3.15  # original 2.5
        self.MAX_HORZ_VELOCITY     = 3.15  # original 2.5
        self.MAX_VERT_ACCEL        = 0.50  # original 0.4
        self.MAX_HORZ_ACCEL        = 0.50  # original 0.4
        self.DECEL_DISTANCE_VERT   = 9.0   # original 12
        self.DECEL_DISTANCE_HORZ   = 12.0  # original 16
        self.VERT_DECEL_SPEED      = 0.4   # original 0.5
        self.HORZ_DECEL_SPEED      = 1.8   # original 2.0
        self.MAX_STABILIZE         = 10    # original 10
        self.SAFE_ALTITUDE         = 60.0  # Must be higher than buildings/terrain -- ask world?
        self.START_ROTOR_SPEED_RPM = 290.0 # Original 360
        self.HEADING_TOL_DEG       = 0.01
        self.TAIL_ROTOR_RANGE      = 10.0
        self.MAX_ROTATE_DELTA      = 6.0
        self.ALTITUDE_MARGIN = 8.0
        self.TAG = "Danook"
        self.FULL_DEBUG_MASK = 0xf000
        self.DEBUG_POS_BIT   = 0x8000
        self.DEBUG_ALT_BIT   = 0x4000
        self.DEBUG_PKG_BIT   = 0x2000
        self.DEBUG_STATE_BIT = 0x1000

        # Control factors ported from Danook Controller
        self.myState = State(State.LANDED)
        self.wasOnGround = False
        self.desMainRotorSpeed_RPM = self.START_ROTOR_SPEED_RPM
        self.desTailRotorSpeed_RPM = 100.0
        self.desPitch_Degrees = 0.0
        self.estimatedAcceleration = None
        self.estimatedVelocity = None
        self.lastPosition = None
        self.actualPosition = None
        self.currentDestination = None
        self.lastTime = 0.0
        self.currTime = 0.0
        self.stableCount = 0
        self.desiredAltitude = self.SAFE_ALTITUDE + self.ALTITUDE_MARGIN

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

    def __headingValid(self) -> bool:
        headingValid = False
        transformation = base.transformations(self.getId())
        if not (self.currentDestination is None or transformation is None):
            headingValid = True
        return headingValid

    def __getHeadingDelta(self, useVelocity) -> float:
        deltaHeading = 0.0
        transformation = base.transformations(self.getId())
        actHeading = transformation.x
        deltaY = self.currentDestination.y - self.actualPosition.y
        deltaX = self.currentDestination.x - self.actualPosition.x
        if useVelocity:
            deltaY = self.estimatedVelocity.y
            deltaX = self.estimatedVelocity.x
        desiredHeading = math.degrees(math.atan2(deltaY, deltaX))
        if desiredHeading < 0.0:
            desiredHeading += 360.0
        deltaHeading = desiredHeading - actHeading
        if deltaHeading < -180.0:
            deltaHeading += 360.0
        elif deltaHeading > 180.0:
            deltaHeading -= 360.0
        return deltaHeading

    def __adjustHeading(self, useVelocity) -> bool:
        headingOK = False
        validHeading = self.__headingValid()
        if validHeading:
            deltaHeading = self.__getHeadingDelta(useVelocity)
            if abs(deltaHeading) < self.HEADING_TOL_DEG:
                self.desTailRotorSpeed_RPM = 100.0
                headingOK = True
            else:
                deltaRotor = (deltaHeading / self.MAX_ROTATE_DELTA) * self.TAIL_ROTOR_RANGE
                if deltaRotor > self.TAIL_ROTOR_RANGE:
                    deltaRotor = self.TAIL_ROTOR_RANGE
                elif deltaRotor < -self.TAIL_ROTOR_RANGE:
                    deltaRotor = -self.TAIL_ROTOR_RANGE
                self.desTailRotorSpeed_RPM = 100.0 + deltaRotor
                base.dbg(self.TAG, "Desired Tail Rotor: {:.2f}, deltaHeading: {:.2f}".format(self.desTailRotorSpeed_RPM, deltaHeading), self.DEBUG_POS_BIT)
        return headingOK

    def __estimateVelocity(self, deltaTime) -> Vec3:
        oldVelocity = None
        if not self.estimatedVelocity is None:
            oldVelocity = Vec3(self.estimatedVelocity)
        self.estimatedVelocity = Vec3((self.actualPosition.x - self.lastPosition.x) / deltaTime, (self.actualPosition.y - self.lastPosition.y) / deltaTime, (self.actualPosition.z - self.lastPosition.z) / deltaTime)
        #base.dbg(self.TAG, "velocity: (" + str(self.estimatedVelocity.x) + ", " + str(self.estimatedVelocity.y) + ", " + str(self.estimatedVelocity.z) + ")", self.DEBUG_POS_BIT )
        return oldVelocity

    def __estimateAcceleration(self, lastVelocity, deltaTime) -> Vec3:
        oldAcceleration = None
        if not self.estimatedAcceleration is None:
            oldAcceleration = Vec3(self.estimatedAcceleration)
        self.estimatedAcceleration = Vec3((self.estimatedVelocity.x - lastVelocity.x) / deltaTime, (self.estimatedVelocity.y - lastVelocity.y) / deltaTime, (self.estimatedVelocity.z - lastVelocity.z) / deltaTime)
        #base.dbg(self.TAG, "acceleration: (" + str(self.estimatedAcceleration.x) + ", " + str(self.estimatedAcceleration.y) + ", " + str(self.estimatedAcceleration.z) + ")", self.DEBUG_POS_BIT )
        return oldAcceleration

    def __estimatePhysics(self) -> bool:
        updated = False
        deltaTime = self.currTime - self.lastTime
        if deltaTime < 0.001:
            base.dbg(self.TAG, "No time change -- no physics estimate",self.DEBUG_POS_BIT)
            return updated
        updated = True
        oldVelocity = self.__estimateVelocity(deltaTime)
        if (not oldVelocity is None):
            self.__estimateAcceleration(oldVelocity, deltaTime)
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
        ratio = deltaValue / DECEL_DISTANCE
        if ratio < 1.0:
            targetVelocity = deltaValue / DECEL_DISTANCE
        if actAlt > desAlt:
            targetVelocity *= -1.0
        return targetVelocity

    def __approachTarget(self, justStop) -> bool:
        success = False
        if self.currentDestination is None and justStop == False:
            base.dbg(self.TAG, "No destination", self.DEBUG_POS_BIT)
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
            targetXVelocity = self.__computeDesiredVelocity(self.actualPosition.x, actualDestination.x, False)
        targetXAcceleration = self.__computeDesiredAcceleration(self.estimatedVelocity.x, targetXVelocity, False)
        xMultiplier = 1.0
        deltaXAcceleration = targetXAcceleration - self.estimatedAcceleration.x
        if deltaXAcceleration > self.MAX_HORZ_ACCEL:
            xMultiplier = self.MAX_HORZ_ACCEL / deltaXAcceleration
        if deltaXAcceleration < -self.MAX_HORZ_ACCEL:
            xMultiplier = (-self.MAX_HORZ_ACCEL) / deltaXAcceleration
        # repeat for Y
        targetYVelocity = 0.0
        if justStop == False:
            targetYVelocity = self.__computeDesiredVelocity(self.actualPosition.y, actualDestination.y, False)
        targetYAcceleration = self.__computeDesiredAcceleration(self.estimatedVelocity.y, targetYVelocity, False)
        yMultiplier = 1.0
        deltaYAcceleration = targetYAcceleration - self.estimatedAcceleration.y
        if deltaYAcceleration > self.MAX_HORZ_ACCEL:
            yMultiplier = self.MAX_HORZ_ACCEL / deltaYAcceleration
        if deltaYAcceleration < -self.MAX_HORZ_ACCEL:
            yMultiplier = (-self.MAX_HORZ_ACCEL) / deltaYAcceleration

        deltaXAcceleration *= xMultiplier
        deltaYAcceleration *= yMultiplier
        # Limit size of the vector but do not change the proportion
        #if xMultiplier < yMultiplier:
            #deltaXAcceleration *= yMultiplier
            #deltaYAcceleration *= yMultiplier
        #else:
            #deltaXAcceleration *= xMultiplier
            #deltaYAcceleration *= xMultiplier
        deltaAcceleration = math.sqrt(deltaXAcceleration * deltaXAcceleration + deltaYAcceleration * deltaYAcceleration)
        accelHeading = math.degrees(math.atan2(deltaYAcceleration, deltaXAcceleration))
        if accelHeading < 0.0:
            accelHeading += 360.0
        transformation = base.transformations(self.getId())
        #deltaAngle = abs(accelHeading - moveHeading)
        deltaAngle = abs(accelHeading - transformation.x)
        if deltaAngle > 90.0:
            deltaAcceleration *= -1.0
        base.dbg(self.TAG, "Dist to target: {:.2f}, Want Accel: {:.2f}, compass heading: {:.2f}, accelHeading: {:.2f}, current pitch: {:.2f}".format(deltaVector.getXy().length(), deltaAcceleration, transformation.x, accelHeading, self.desPitch_Degrees), self.DEBUG_POS_BIT)
        self.desPitch_Degrees += deltaAcceleration * self.HORZ_CONTROL_FACTOR
        if justStop:
            deltaVx = self.estimatedVelocity.x
            deltaVy = self.estimatedVelocity.y
            base.dbg(self.TAG, "Trying to stop -- vel: ({:.2f}, {:.2f})".format(self.estimatedVelocity.x, self.estimatedVelocity.y), self.DEBUG_POS_BIT)
            delta = math.sqrt(deltaVx * deltaVx + deltaVy * deltaVy)
            if delta < 0.1:
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
            # This might be where we screw up
            if distance > 4.0:
                self.desiredAltitude = self.SAFE_ALTITUDE + self.ALTITUDE_MARGIN
        else:
            base.dbg(self.TAG, "No destination yet", self.DEBUG_ALT_BIT)

    def __controlAltitude(self, inState) -> State:
        outState = inState
        if self.estimatedVelocity is None or self.estimatedAcceleration is None:
            return outState
        flightState = self.actualPosition.getZ() > 0.0
        onGround = flightState == 0
        if onGround:
            base.dbg(self.TAG, "On the ground...", self.DEBUG_ALT_BIT)
            if inState == State.APPROACHING:
                outState = State.LANDED
                self.desPitch_Degrees = 0.0
                # Decrease rotor speed 10% to avoid taking off again
                self.desMainRotorSpeed_RPM *= 0.90
            if not self.currentDestination is None:
                deltaX = self.currentDestination.x - self.actualPosition.x
                deltaY = self.currentDestination.y - self.actualPosition.y
                actDistance = math.sqrt(deltaX * deltaX + deltaY * deltaY)
                if (actDistance < base.MAX_PACKAGE_DISTANCE):
                    delivered = base.deliverPackage(self.getId())
                    if self.wasOnGround == False:
                        base.dbg(self.TAG, "Time: {:.2f} -- trying to deliver package at ({:.2f}, {:.2f})".format(self.currTime, self.actualPosition.x,self.actualPosition.y), self.DEBUG_PKG_BIT)
                    if delivered:
                        #TODO: Delete waypoint if world didn't
                        if self.wasOnGround == False:
                            base.dbg(self.TAG, "Time: {:.2f} -- Delivered a package".format(self.currTime), self.DEBUG_PKG_BIT)
                        self.currentDestination = None
                    else:
                        onGround = False
                    self.desiredAltitude = self.SAFE_ALTITUDE + self.ALTITUDE_MARGIN
                    outState = State.CLIMB
                else:
                    if self.wasOnGround == False:
                        base.dbg(self.TAG, "Time: {:.2f} -- Too far to deliver package: act: {:.2f}, tol: {:.2f}".format(self.currTime, actDistance, base.MAX_PACKAGE_DISTANCE), self.DEBUG_PKG_BIT)
            else:
                if self.wasOnGround == False:
                    base.dbg(self.TAG, "Time: {:.2f} Landed with no destination?".format(self.currTime), self.DEBUG_PKG_BIT)
            self.wasOnGround = onGround
        else:
            if inState == State.LANDED:
                outState = State.CLIMB
            self.wasOnGround = False
        targetVertVelocity = self.__computeDesiredVelocity(self.actualPosition.z, self.desiredAltitude, True)
        targetVertAcceleration = self.__computeDesiredAcceleration(self.estimatedVelocity.z, targetVertVelocity, True)
        deltaAcceleration = targetVertAcceleration - self.estimatedAcceleration.z
        if deltaAcceleration > self.MAX_VERT_ACCEL:
            deltaAcceleration = self.MAX_VERT_ACCEL
        if deltaAcceleration < (-self.MAX_VERT_ACCEL):
            deltaAcceleration = -self.MAX_VERT_ACCEL
        base.dbg(self.TAG, "ActHeight: {:.2f}, desHeight: {:.2f}, actVel: {:.2f}, targetVel: {:.2f}, actAccel: {:.2f}, targetAccel: {:.2f}, deltaAccel: {:.2f}".format(self.actualPosition.z,self.desiredAltitude,self.estimatedVelocity.z, targetVertVelocity, self.estimatedAcceleration.z, targetVertAcceleration, deltaAcceleration), self.DEBUG_ALT_BIT)
        self.desMainRotorSpeed_RPM += deltaAcceleration * self.VERT_CONTROL_FACTOR
        base.requestSettings(self.getId(), self.desMainRotorSpeed_RPM, self.desPitch_Degrees, self.desTailRotorSpeed_RPM)
        return outState

    def __isSafeAltitude(self, climbing) -> bool:
        # TODO: Scan radar in direction of target for obstacles
        deltaX = self.currentDestination.x - self.actualPosition.x
        deltaY = self.currentDestination.y - self.actualPosition.y
        retVal = True
        if deltaX > self.DECEL_DISTANCE_HORZ or deltaY > self.DECEL_DISTANCE_HORZ:
            if self.actualPosition.z > self.SAFE_ALTITUDE:
                retVal = True
            else:
                retVal = False
        else:
            if climbing:
                retVal = self.actualPosition.z > self.SAFE_ALTITUDE
            else:
                retVal = True
        base.dbg(self.TAG, "Altitude Safety check result: (climbing? " + str(climbing) + ")" + str(retVal) + " Altitude: " + str(self.actualPosition.z), self.DEBUG_ALT_BIT)
        return retVal

    def __controlTheShip(self, isCloser):
        if self.myState == State.APPROACHING and isCloser == False:
            self.myState = State.STOP_NOW
        nextState = self.myState
        base.dbg(self.TAG, "Control the ship -- state: " + str(self.myState), self.DEBUG_STATE_BIT)
        match self.myState:
            case State.LANDED:
                pass
            case State.CLIMB:
                if self.__isSafeAltitude(True):
                    nextState = State.FINDING_HEADING
            case State.FINDING_HEADING:
                headingOK = self.__adjustHeading(False)
                if headingOK:
                    nextState = State.STABILIZE_ROTATION
                    self.stableCount = 0
            case State.STABILIZE_ROTATION:
                headingValid = self.__headingValid()
                if headingValid:
                    headingOK = self.__getHeadingDelta(False)
                    self.stableCount += 1
                else:
                    self.stableCount = 0
                    base.dbg(self.TAG, "STABILIZE: Heading fluctuated... waiting", self.DEBUG_POS_BIT)
                if self.stableCount >= self.MAX_STABILIZE:
                    nextState = State.APPROACHING
            case State.APPROACHING:
                self.__selectDesiredAltitude()
                self.__approachTarget(False)
            case State.STOP_NOW:
                # stop spinning
                self.desTailRotorSpeed_RPM = 100.0 # Stable
                success = self.__approachTarget(True)
                if success:
                    nextState = State.FINDING_HEADING
            case State.TASKS_COMPLETE:
                self.desMainRotorSpeed_RPM = 0.0
                self.desiredAltitude = 0.0
                base.dbg(self.TAG, "Time: {:.2f} -- All packages delivered.  (Powering Down)".format(self.currTime),self.FULL_DEBUG_MASK)
                nextState = State.POWER_DOWN
            case State.POWER_DOWN:
                pass
            case _:
                base.dbg(self.TAG, "Unexpected State", self.DEBUG_STATE_BIT)
                raise RuntimeError
        self.myState = nextState
        if self.myState != State.POWER_DOWN:
            self.myState = self.__controlAltitude(self.myState)

    def update(self,dt,tick):
        StigChopper.update(self,dt,tick)
        #transformation = base.transformations(self.getId())
        # I added the negative sign because pitch looked backwards to me
        #self.actor.setHpr(transformation.x, -transformation.y, transformation.z)

    def runLogic(self,currentTime,elapsedTime):
        startTime = time.time_ns()
        self.actualPosition = base.gps(self.getId())
        self.currTime = currentTime
        if self.currentDestination is None:
            self.currentDestination = self.__findClosestDestination()
            if not self.currentDestination is None:
                base.dbg(self.TAG, "Got a destination ({:2} points remaining)".format(len(self.targetWaypoints)), self.DEBUG_PKG_BIT)
            else:
                if self.myState != State.POWER_DOWN:
                    self.myState = State.TASKS_COMPLETE
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
                        base.dbg(self.TAG, "Wrong way now: " + str(newDistance) + " then: " + str(oldDistance), self.DEBUG_POS_BIT)
                self.__controlTheShip(closer)
            else:
                base.dbg(self.TAG, "No physics estimate?", self.DEBUG_POS_BIT)
        self.lastTime = self.currTime
        self.lastPosition = Vec4(self.actualPosition)
        endTime = time.time_ns()
        #base.dbg(self.TAG, "Ran Logic in: {} ns".format(endTime-startTime), 0x10000)