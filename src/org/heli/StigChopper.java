package org.heli;

/** This class represents our chopper and its capabilities
 * 
 * @author Daniel LaFuze
 * Copyright 2015
 * All Rights Reserved
 *
 */
public class StigChopper {
	
	Point3D size;
	
	World world;
	
	int id;
	
	private static final double BASE_MASS = 100.0; // kg
	
	// Total Capacity can be divided however desired between cargo and fuel
	private static final double TOTAL_CAPACITY = 300.0; // kg
	
	private static final double MAX_MAIN_ROTOR_SPEED = 400.0; // RPM
	
	private static final double MAX_TAIL_ROTOR_SPEED = 120.0; // RPM
	private static final double MIN_TAIL_ROTOR_SPEED = 80.0; // RPM
	
	private static final double X_SIZE = 2.0;
	private static final double Y_SIZE = 5.0;
	private static final double Z_SIZE = 3.0;
	
	private double currentFuelWeight;
	
	private double mainRotorRPM;
	
	private double tailRotorRPM;
	
	private double currentPitch; // degrees
	
	private double cargoMass; // kg
	
	private double fuelMass; // kg

	private double heading; // degrees
	
	private boolean landed;
	
	public double currentMass() {
		return cargoMass + fuelMass + BASE_MASS;
	}
	
	public StigChopper(int chopperID, World theWorld) {
		id = chopperID;
		world = theWorld;
		cargoMass = TOTAL_CAPACITY / 2.0;
		fuelMass = TOTAL_CAPACITY / 2.0;
		size = new Point3D(X_SIZE, Y_SIZE, Z_SIZE);
		mainRotorRPM = 0.0;
		tailRotorRPM = 0.0;
		currentPitch = 0.0;
		heading = 0.0;
		landed = true;
	}
	
	public Point3D getSize() {
		Point3D result = new Point3D(X_SIZE, Y_SIZE, Z_SIZE);
		return result;
	}
}
