/** Copyright 2015, Dan and Sasha
 * 
 */
package org.heli;

/** The world uses this class to maintain all necessary flight information
 * about a chopper.
 * @author Daniel LaFuze
 *
 */
public class ChopperInfo {
	
	private World myWorld;
	
	int chopperID;
	
	double currentFuel_kg;
	
	private static final double THRUST_PER_RPM = 11.1111; // N (kg * m/s^2)
	
	public static final double MAX_MAIN_ROTOR_SPEED = 400.0; // RPM
	
	private static final double EARTH_ACCELERATION = -9.80665; // m/s^2
	
	public static final double MAX_TAIL_ROTOR_SPEED = 120.0; // RPM
	public static final double STABLE_TAIL_ROTOR_SPEED = 100.0; // RPM
	public static final double MIN_TAIL_ROTOR_SPEED = 80.0; // RPM
	
	public static final double MAX_TILT_MAGNITUDE = 5.0; // Degrees
	
	private static final double MAX_MAIN_ROTOR_DELTA = 60.0; // RPM per Second
	
	private static final double MAX_TAIL_ROTOR_DELTA = 15.0; // RPM per Second
	
	private static final double MAX_TILT_DELTA = 3.0; // Degrees per second
	
	private static final double FUEL_PER_REVOLUTION = 1.0 / 60.0; // Liters
	
	private static final double ROTATION_PER_TAIL_RPM = 3.0; // degrees per second
	
	private double actMainRotorSpeed_RPM;
	
	private double actTailRotorSpeed_RPM;
	
	private double actTilt_Degrees;
	
	private double desMainRotorSpeed_RPM;
	
	private double desTailRotorSpeed_RPM;
	
	private double desTilt_Degrees;
	
	private double remainingFuel_kg;
	
	private boolean takenOff = false;
	
	// In meters per second squared
	private Point3D actAcceleration_ms2;
	
	// In meters per second
	private Point3D actVelocity_ms;
	
	// In meters
	private Point3D actPosition_m;
	
	double heading_Degrees;

	/** Constructs a ChopperInfo object with a chopper on the ground
	 * 
	 * @param myWorld The world (for interface)
	 * @param chopperID To get information about chopper -- such as weight
	 * @param startPos Where will the chopper start
	 * @param startHeading Which way is chopper facing?
	 */
	public ChopperInfo(World world, int id, Point3D startPos, double startHeading) {
		myWorld = world;
		chopperID = id;
		actPosition_m = startPos;
		heading_Degrees = startHeading;
		actMainRotorSpeed_RPM = 0.0;
		actTailRotorSpeed_RPM = 0.0;
		actTilt_Degrees = 0.0;
		desMainRotorSpeed_RPM = 0.0;
		desTailRotorSpeed_RPM = 0.0;
		desTilt_Degrees = 0.0;
		actAcceleration_ms2 = new Point3D(0.0, 0.0, 0.0);
		actVelocity_ms = new Point3D(0.0, 0.0, 0.0);
		StigChopper thisChopper = myWorld.getChopper(chopperID);
		remainingFuel_kg = 0.0;
		if (thisChopper != null)
		{
			remainingFuel_kg = thisChopper.fuelCapacity();
		}
	}
	
	public Point3D getPosition()
	{
		return actPosition_m;
	}
	
	public double getHeading()
	{
		return heading_Degrees;
	}
	
	public double getTilt()
	{
		return actTilt_Degrees;
	}
	
	public void requestMainRotorSpeed(double newSpeed)
	{
		desMainRotorSpeed_RPM = newSpeed;
	}
	
	public void requestTailRotorSpeed(double newSpeed)
	{
		desTailRotorSpeed_RPM = newSpeed;
	}
	
	public void requestTiltLevel(double newTilt)
	{
		desTilt_Degrees = newTilt;
	}
	
	private void updateMainRotorSpeed(double elapsedTime)
	{
		double deltaMainRotor = MAX_MAIN_ROTOR_DELTA * elapsedTime;
		if (desMainRotorSpeed_RPM > MAX_MAIN_ROTOR_SPEED)
		{
			desMainRotorSpeed_RPM = MAX_MAIN_ROTOR_SPEED;
		}
		if (actMainRotorSpeed_RPM < desMainRotorSpeed_RPM)
		{
			actMainRotorSpeed_RPM += deltaMainRotor;
			if (actMainRotorSpeed_RPM > desMainRotorSpeed_RPM)
			{
				actMainRotorSpeed_RPM = desMainRotorSpeed_RPM;
			}
		}
		else if (actMainRotorSpeed_RPM > desMainRotorSpeed_RPM)
		{
			actMainRotorSpeed_RPM -= deltaMainRotor;
			if (actMainRotorSpeed_RPM < desMainRotorSpeed_RPM)
			{
				actMainRotorSpeed_RPM = desMainRotorSpeed_RPM;
			}
		}
	}
	
	public void updateTailRotorSpeed(double elapsedTime)
	{
		double deltaTailRotor = MAX_TAIL_ROTOR_DELTA * elapsedTime;
		if (desTailRotorSpeed_RPM > MAX_TAIL_ROTOR_SPEED)
		{
			desTailRotorSpeed_RPM = MAX_TAIL_ROTOR_SPEED;
		}
		if (actTailRotorSpeed_RPM < desTailRotorSpeed_RPM)
		{
			actTailRotorSpeed_RPM += deltaTailRotor;
			if (actTailRotorSpeed_RPM > desTailRotorSpeed_RPM)
			{
				actTailRotorSpeed_RPM = desTailRotorSpeed_RPM;
			}
		}
		else if (actTailRotorSpeed_RPM > desTailRotorSpeed_RPM)
		{
			actTailRotorSpeed_RPM -= deltaTailRotor;
			if (actTailRotorSpeed_RPM < desTailRotorSpeed_RPM)
			{
				actTailRotorSpeed_RPM = desTailRotorSpeed_RPM;
			}
		}
	}
	
	public void updateTiltLevel(double elapsedTime)
	{
		double deltaTailRotor = MAX_TAIL_ROTOR_DELTA * elapsedTime;
		if (desTilt_Degrees > MAX_TILT_MAGNITUDE)
		{
			desTilt_Degrees = MAX_TILT_MAGNITUDE;
		}
		if (desTilt_Degrees < -MAX_TILT_MAGNITUDE)
		{
			desTilt_Degrees = -MAX_TILT_MAGNITUDE;
		}
		double deltaTilt = MAX_TILT_DELTA * elapsedTime;
		if (actTilt_Degrees < desTilt_Degrees)
		{
			actTilt_Degrees += deltaTilt;
			if (actTilt_Degrees > desTilt_Degrees)
			{
				actTilt_Degrees = desTilt_Degrees;
			}
		}
		else if (actTilt_Degrees > desTilt_Degrees)
		{
			actTilt_Degrees -= deltaTilt;
			if (actTilt_Degrees < desTilt_Degrees)
			{
				actTilt_Degrees = desTilt_Degrees;
			}
		}
	}

	public boolean updateFuelRemaining(double elapsedTime)
	{
		boolean outOfGas = false;
		double rotorRevolutions = actMainRotorSpeed_RPM * elapsedTime;
		currentFuel_kg -= rotorRevolutions * FUEL_PER_REVOLUTION;
		if (currentFuel_kg < 0)
		{
			outOfGas = true;
		}
		return outOfGas;
		
	}
	
	public void updateCurrentHeading(double elapsedTime)
	{
		double rotationCalculator = actTailRotorSpeed_RPM;
		if (rotationCalculator < MIN_TAIL_ROTOR_SPEED)
		{
			rotationCalculator = MIN_TAIL_ROTOR_SPEED;
		}
		else if (rotationCalculator > MAX_TAIL_ROTOR_SPEED)
		{
			rotationCalculator = MAX_TAIL_ROTOR_SPEED;
		}
		double rotorSetting = rotationCalculator - STABLE_TAIL_ROTOR_SPEED;
		heading_Degrees += (rotorSetting * ROTATION_PER_TAIL_RPM) * elapsedTime;
	}
	
	public void fly(double elapsedTime)
	{
		boolean outOfGas = updateFuelRemaining(elapsedTime);
		if (outOfGas)
		{
			desMainRotorSpeed_RPM = 0.0;
			desTailRotorSpeed_RPM = 0.0;
			desTilt_Degrees = 0.0;
		}
		updateMainRotorSpeed(elapsedTime);
		updateTailRotorSpeed(elapsedTime);
		updateTiltLevel(elapsedTime);
		double cargoMass_kg = 0.0;
		StigChopper thisChopper = myWorld.getChopper(chopperID);
		if (thisChopper != null)
		{
			cargoMass_kg = ChopperAggregator.ITEM_WEIGHT * thisChopper.itemCount();
		}
		double totalMass_kg = cargoMass_kg + currentFuel_kg + ChopperAggregator.BASE_MASS;
		double downForce_N = totalMass_kg * EARTH_ACCELERATION;
		double actTilt_radians = actTilt_Degrees * Math.PI / 180.0;
		double liftForce_N = actMainRotorSpeed_RPM * THRUST_PER_RPM * Math.cos(actTilt_radians);
		// lateral force will only be used when off the ground (See below)
		double lateralForce_N = actMainRotorSpeed_RPM * THRUST_PER_RPM * Math.sin(actTilt_radians);
		double deltaForce_N = liftForce_N - downForce_N;
		if (deltaForce_N > 0.0) // We have enough force to ascend
		{
			// We know vertical force, we'll compute lateral forces next
			actAcceleration_ms2.m_z = deltaForce_N;
			if (takenOff == false)
			{
				takenOff = true;
			}
		}
		else
		{
			// TODO: Determine if we're sitting on the ground, for now, it's treated SIMPLE
			// This means that once you take off, you can go under the world
			if (takenOff == true)
			{
				actAcceleration_ms2.m_z = deltaForce_N;
			}
			else
			{
				actAcceleration_ms2.m_z = 0.0;
			}
		}
		if (takenOff) // Tail rotor comes into play
		{
			updateCurrentHeading(elapsedTime);
			// Now that we have our heading, we can compute the direction of our thrust
			double heading_radians = heading_Degrees * Math.PI / 180.0;
			actAcceleration_ms2.m_x = Math.cos(heading_radians);
			actAcceleration_ms2.m_y = Math.sin(heading_radians);
		}
		else
		{
			// For now, we're preventing skating -- chopper sliding along the ground
			actAcceleration_ms2.m_x = 0.0;
			actAcceleration_ms2.m_y = 0.0;
		}
		// now that accurate acceleration is computed, we can compute new velocity
		actVelocity_ms.m_x += (actAcceleration_ms2.m_x * elapsedTime);
		actVelocity_ms.m_y += (actAcceleration_ms2.m_y * elapsedTime);
		actVelocity_ms.m_z += (actAcceleration_ms2.m_z * elapsedTime);
		// Now that accurate velocity is computed, we can update position
		actPosition_m.m_x += (actVelocity_ms.m_x * elapsedTime);
		actPosition_m.m_y += (actVelocity_ms.m_y * elapsedTime);
		actPosition_m.m_z += (actVelocity_ms.m_z * elapsedTime);
		show();
	}
	
	public void show()
	{
		System.out.println("Main Rotor RPM: " + actMainRotorSpeed_RPM);
		System.out.println("Acceleration: " + actAcceleration_ms2.info());
	}
}
