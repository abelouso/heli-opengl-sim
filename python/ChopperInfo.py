#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

from panda3d.core import Vec3, Vec4

import math
import random


class ChopperInfo:
    def __init__(self, id, fuelCap, startPos, startHeading):
        self.TAG = "ChopperInfo"
        self.CI_DBG = 0x20000000
        self.THRUST_PER_RPM = 11.1111 # N (kg * m/s^2)
        self.MAX_MAIN_ROTOR_SPEED = 400.0 # RPM
        self.EARTH_ACCELERATION = 9.80665 # m/s^2
        self.MAX_TAIL_ROTOR_SPEED = 120.0 # RPM
        self.STABLE_TAIL_ROTOR_SPEED = 100.0 # RPM
        self.MIN_TAIL_ROTOR_SPEED = 80.0 # RPM
        self.MAX_TILT_MAGNITUDE = 10.0 # Degrees
        self.MAX_MAIN_ROTOR_DELTA = 60.0 # RPM per Second
        self.MAX_TAIL_ROTOR_DELTA = 30.0 # RPM per Second
        self.MAX_TILT_DELTA = 3.0 # Degrees per second
        self.FUEL_PER_REVOLUTION = 1.0 / 60.0 # Liters
        self.ROTATION_PER_TAIL_RPM = 3.0 # degrees per second

        self.chopperID = id
        self.mainRotorPosition_Degrees = 0.0 # This is needed to draw the rotor
        self.tailRotorPosition_Degrees = 0.0 # This is needed to draw the rotor
        
        self.actMainRotorSpeed_RPM = 0.0
        self.actTailRotorSpeed_RPM = 0.0
        self.actTilt_Degrees = 0.0
        self.desMainRotorSpeed_RPM = 0.0
        self.desTailRotorSpeed_RPM = 0.0
        self.desTilt_Degrees = 0.0
        self.remainingFuel_kg = fuelCap
        self.takenOff = False
        # In meters per second squared
        self.actAcceleration_ms2 = Vec3(0.0, 0.0, 0.0)
        # In meters per second
        self.actVelocity_ms = Vec3(0.0, 0.0, 0.0)
        # In meters
        self.actPosition_m = Vec4(startPos.getX(), startPos.getY(), startPos.getZ(),0.0)
        self.heading_Degrees = startHeading
        self.m_revs_sum = 0.0
        self.m_burnt_sum = 0.0
        self.m_time_sum = 0.0

    def getFuelRemaining(self):
        return self.remainingFuel_kg


    def getMainRotorPosition(self):
        return self.mainRotorPosition_Degrees
	
	
    def getTailRotorPosition(self):
        return self.tailRotorPosition_Degrees
	
        
    def getPosition(self):
        return self.actPosition_m
	
	
    def getHeading(self):
        return self.heading_Degrees
	
	
    def getTilt(self):
        return self.actTilt_Degrees
	
    def requestMainRotorSpeed(self, newSpeed):
        if (self.remainingFuel_kg > 0.0):
            self.desMainRotorSpeed_RPM = newSpeed
	
    def requestTailRotorSpeed(self, newSpeed):
        if (self.remainingFuel_kg > 0.0):
            self.desTailRotorSpeed_RPM = newSpeed
	
    def requestTiltLevel(self, newTilt):
        if (self.remainingFuel_kg > 0.0):
            self.desTilt_Degrees = newTilt
		
    def updateMainRotorSpeed(self, elapsedTime):
        deltaMainRotor = self.MAX_MAIN_ROTOR_DELTA * elapsedTime
        
        if (self.desMainRotorSpeed_RPM > self.MAX_MAIN_ROTOR_SPEED):
            self.desMainRotorSpeed_RPM = self.MAX_MAIN_ROTOR_SPEED
            
        if (self.actMainRotorSpeed_RPM < self.desMainRotorSpeed_RPM):
            self.actMainRotorSpeed_RPM += deltaMainRotor
            
            if (self.actMainRotorSpeed_RPM > self.desMainRotorSpeed_RPM):
                self.actMainRotorSpeed_RPM = self.desMainRotorSpeed_RPM
        
        elif (self.actMainRotorSpeed_RPM > self.desMainRotorSpeed_RPM):
        
            self.actMainRotorSpeed_RPM -= deltaMainRotor
            if (self.actMainRotorSpeed_RPM < self.desMainRotorSpeed_RPM):
                self.actMainRotorSpeed_RPM = self.desMainRotorSpeed_RPM
            
        
        # 1 RPM = 6 degrees per second
        self.mainRotorPosition_Degrees += self.actMainRotorSpeed_RPM * elapsedTime * 60.0
        while (self.mainRotorPosition_Degrees >= 360.0):
            self.mainRotorPosition_Degrees -= 360.0 # Just for drawing
	
    def updateTailRotorSpeed(self, elapsedTime):
        
        deltaTailRotor = self.MAX_TAIL_ROTOR_DELTA * elapsedTime
        if (self.desTailRotorSpeed_RPM > self.MAX_TAIL_ROTOR_SPEED):
        
            self.desTailRotorSpeed_RPM = self.MAX_TAIL_ROTOR_SPEED
        
        if (self.actTailRotorSpeed_RPM < self.desTailRotorSpeed_RPM):
        
            self.actTailRotorSpeed_RPM += deltaTailRotor
            if (self.actTailRotorSpeed_RPM > self.desTailRotorSpeed_RPM):
            
                self.actTailRotorSpeed_RPM = self.desTailRotorSpeed_RPM
            
        
        elif (self.actTailRotorSpeed_RPM > self.desTailRotorSpeed_RPM):
        
            self.actTailRotorSpeed_RPM -= deltaTailRotor
            if (self.actTailRotorSpeed_RPM < self.desTailRotorSpeed_RPM):
            
                self.actTailRotorSpeed_RPM = self.desTailRotorSpeed_RPM
        
        # 1 RPM = 6 degrees per second
        self.tailRotorPosition_Degrees += self.actTailRotorSpeed_RPM * elapsedTime * 60.0
        while (self.tailRotorPosition_Degrees >= 360.0):
        
            self.tailRotorPosition_Degrees -= 360.0 # Just for drawing
		
	
	
    def updateTiltLevel(self, elapsedTime):
        
        deltaTailRotor = self.MAX_TAIL_ROTOR_DELTA * elapsedTime
        if (self.desTilt_Degrees > self.MAX_TILT_MAGNITUDE):
        
            self.desTilt_Degrees = self.MAX_TILT_MAGNITUDE
        
        if (self.desTilt_Degrees < -self.MAX_TILT_MAGNITUDE):
        
            self.desTilt_Degrees = -self.MAX_TILT_MAGNITUDE
        
        deltaTilt = self.MAX_TILT_DELTA * elapsedTime
        if (self.actTilt_Degrees < self.desTilt_Degrees):
        
            self.actTilt_Degrees += deltaTilt
            if (self.actTilt_Degrees > self.desTilt_Degrees):
                self.actTilt_Degrees = self.desTilt_Degrees
            
        elif (self.actTilt_Degrees > self.desTilt_Degrees):
        
            self.actTilt_Degrees -= deltaTilt
            if (self.actTilt_Degrees < self.desTilt_Degrees):
            
                self.actTilt_Degrees = self.desTilt_Degrees
			
		
	
    def updateFuelRemaining(self, elapsedTime):
        
        outOfGas = False
        rotorRevolutions = self.actMainRotorSpeed_RPM / 60.0 * elapsedTime
        fuelBurned = rotorRevolutions * self.FUEL_PER_REVOLUTION
        self.remainingFuel_kg -= fuelBurned
        self.m_revs_sum += rotorRevolutions
        self.m_burnt_sum += fuelBurned
        self.m_time_sum += elapsedTime
        if (self.remainingFuel_kg < 0):
        
            base.dbg(self.TAG,"Out of Gas!",self.CI_DBG)
            self.remainingFuel_kg = 0.0
            outOfGas = True
        
        return outOfGas
		
	
	
    def updateCurrentHeading(self, elapsedTime):
        
        rotationCalculator = self.actTailRotorSpeed_RPM
        if (rotationCalculator < self.MIN_TAIL_ROTOR_SPEED):
        
            rotationCalculator = self.MIN_TAIL_ROTOR_SPEED
        
        elif (rotationCalculator > self.MAX_TAIL_ROTOR_SPEED):
        
            rotationCalculator = self.MAX_TAIL_ROTOR_SPEED
        
        rotorSetting = rotationCalculator - self.STABLE_TAIL_ROTOR_SPEED
        self.heading_Degrees += (rotorSetting * self.ROTATION_PER_TAIL_RPM) * elapsedTime
        while (self.heading_Degrees > 360.0):
        
            self.heading_Degrees -= 360.0
        
        while (self.heading_Degrees < 0.0):
        
            self.heading_Degrees += 360.0
		
	
	
    def fly(self, currentTime,  elapsedTime):
        outOfGas = self.updateFuelRemaining(elapsedTime)
        if (outOfGas):
            self.desMainRotorSpeed_RPM *= 0.99
            self.desTailRotorSpeed_RPM *= 0.99
            self.desTilt_Degrees += -1.5 + 2.0 * random.randint(0,100) * 0.01
        
        self.updateMainRotorSpeed(elapsedTime)
        self.updateTailRotorSpeed(elapsedTime)
        self.updateTiltLevel(elapsedTime)
        cargoMass_kg = 0.0
        thisChopper = base.getChopper(self.chopperID)
        if (thisChopper is not None):
            cargoMass_kg = base.ITEM_WEIGHT * thisChopper.itemCount()
        
        totalMass_kg = cargoMass_kg + self.remainingFuel_kg + base.CHOPPER_BASE_MASS
        downForce_N = totalMass_kg * self.EARTH_ACCELERATION # F = mA
        actTilt_radians = math.radians(self.actTilt_Degrees)
        liftForce_N = self.actMainRotorSpeed_RPM * self.THRUST_PER_RPM * math.cos(actTilt_radians)
        # lateral force will only be used when off the ground (See below)
        lateralForce_N = self.actMainRotorSpeed_RPM * self.THRUST_PER_RPM * math.sin(actTilt_radians)
        lateralAcceleration = lateralForce_N / totalMass_kg
        deltaForce_N = liftForce_N - downForce_N
        if (deltaForce_N > 0.0): # We have enough force to ascend
            # We know vertical force, we'll compute lateral forces next
            self.actAcceleration_ms2.setZ(deltaForce_N / totalMass_kg)
            if (self.takenOff == False):
                base.dbg(self.TAG,f"Chopper {self.chopperID} has lifted off!",self.CI_DBG)
                self.takenOff = True
        else: 
            # Simple landing check when close to zero
            if (self.actPosition_m.getZ() < 0.25):
                lateralMagnitude = self.actVelocity_ms.getXy().length()
                base.dbg(self.TAG, "Chopper " + str(self.chopperID) + " Landing check lateral velocity: " + str(lateralMagnitude) + ", vert Velocity: " + str(self.actVelocity_ms.getZ()), self.CI_DBG)
                if (lateralMagnitude < 0.25 and (self.actVelocity_ms.getZ() > (-2.0) and self.actVelocity_ms.getZ() < 0)):
                
                    if (self.takenOff == True):
                        base.dbg(self.TAG,f"Chopper {self.chopperID} has landed!",self.CI_DBG)
                    self.takenOff = False
                
            
            if (self.takenOff == True):
                self.actAcceleration_ms2.setZ( deltaForce_N / totalMass_kg )
            else: 
                self.actAcceleration_ms2.setZ(0.0)
                self.actVelocity_ms.setZ(0.0)
                self.actPosition_m.setZ(0.0)
            
        if (self.takenOff): # Tail rotor comes into play
            self.updateCurrentHeading(elapsedTime)
            # Now that we have our heading, we can compute the direction of our thrust
            heading_radians = math.radians(self.heading_Degrees)
            self.actAcceleration_ms2.setX(lateralAcceleration * math.sin(heading_radians))
            self.actAcceleration_ms2.setY(lateralAcceleration * math.cos(heading_radians))
        else: 
            # For now, we're preventing skating -- chopper sliding along the ground
            self.actAcceleration_ms2.setX(0.0)
            self.actAcceleration_ms2.setY(0.0)
            self.actVelocity_ms.setX(0.0)
            self.actVelocity_ms.setY(0.0)
        
        # now that accurate acceleration is computed, we can compute new velocity
        self.actVelocity_ms.setX((self.actVelocity_ms.getX() + self.actAcceleration_ms2.getX() * elapsedTime))
        self.actVelocity_ms.setY((self.actVelocity_ms.getY() + self.actAcceleration_ms2.getY() * elapsedTime))
        self.actVelocity_ms.setZ((self.actVelocity_ms.getZ() + self.actAcceleration_ms2.getZ() * elapsedTime))
        # Now that accurate velocity is computed, we can update position
        self.actPosition_m.addX((self.actVelocity_ms.getX() * elapsedTime))
        self.actPosition_m.addY((self.actVelocity_ms.getY() * elapsedTime))
        self.actPosition_m.addZ((self.actVelocity_ms.getZ() * elapsedTime))
        self.actPosition_m.setW(currentTime)
	
    def onGround(self,):
        return not self.takenOff
	
    def show(self, curTime):
        base.dbg(self.TAG,f"Heading: {self.heading_Degrees} deg, desired rotor speed: {self.desMainRotorSpeed_RPM}",self.CI_DBG)
        #World.dbg(self.TAG,"World Time: " + curTime + ", Acceleration: " + self.actAcceleration_ms2.info(),self.CI_DBG)
        #World.dbg(self.TAG,"Actual Heading: " + self.heading_Degrees + " Degrees, Velocity: " + self.actVelocity_ms.info(),self.CI_DBG)
        #World.dbg(self.TAG,"Actual Tilt: " + self.actTilt_Degrees + " Degrees, Position: " + self.actPosition_m.info(),self.CI_DBG)
	


	
	