/** Copyright 2015, Sasha and Dan
 * 
 */
package org.heli;

import java.util.ArrayList;

/** This class will control a Danook Helicopter
 * 
 * @author Daniel
 *
 */
public class DanookController extends Thread
{
	// TODO: Implement a state machine
	private int STATE_LANDED = 0;
	private int STATE_CLIMBING = 1;
	private int APPROACHING_TARGET = 2;
	private int STATE_DESCENDING = 3;
	
	private static final double VERT_CONTROL_FACTOR = 6.0;
	
	private Danook myChopper;
	private World myWorld;
	
    private double desMainRotorSpeed_RPM = 0.0;
    private double desTailRotorSpeed_RPM = 0.0;
    private double desTilt_Degrees = 0.0;
    
    private Point3D estimatedAcceleration;
    private Point3D estimatedVelocity;
    private Point3D actualPosition;
    
    public double desiredHeading;
    public double desiredAltitude;
    
    private Point3D currentDestination;
    
	public DanookController(Danook chopper, World world)
	{
		super();
		myChopper = chopper;
		myWorld = world;
        desMainRotorSpeed_RPM = 360.0;
        desTailRotorSpeed_RPM = ChopperInfo.STABLE_TAIL_ROTOR_SPEED;
        desTilt_Degrees = 0.0;
        estimatedAcceleration = new Point3D();
        estimatedVelocity = new Point3D();
        actualPosition = new Point3D();
        desiredHeading = 0.0;
        desiredAltitude = 0.0;
        
        currentDestination = null;
	}

    @Override
    public void run()
    {
    	// Allow constructors to startup
		try
		{
			Thread.sleep(1);
			myWorld.requestSettings(myChopper.getId(), desMainRotorSpeed_RPM, desTilt_Degrees, desTailRotorSpeed_RPM);
		}
		catch (Exception e)
		{
			System.out.println("Caught an exception");
		}
		Point3D lastPosition = null;
		double currTime = 0.0;
		double lastTime = 0.0;
    	while (true)
    	{
    		try
    		{
    			// Do smart stuff...
    			Thread.sleep(2);
    			// TODO: Make these two methods atomic
    			actualPosition = myWorld.gps(myChopper.getId());
    			currTime = myWorld.getTimestamp();
    			if (currentDestination == null)
    			{
    				//currentDestination = findClosestDestination();
    				//System.out.println("DC:Got a destination: " + currentDestination.info());
    			}
    			if (lastPosition != null && lastTime < currTime)
    			{
    				boolean updated = estimatePhysics(currTime, lastPosition, lastTime);
    				if (updated)
    				{
    					controlTheShip();
    				}
    				else
    				{
    					System.out.println("DC: No physics estimate?");
    				}
    			}
    			lastPosition = actualPosition.copy();
    			lastTime = currTime;
    		}
    		catch (Exception e)
    		{
    			System.out.println("Caught an exception: " + e.toString());
    		}
    	}
    }
    
    /** This method attempts to update estimated physics based on what we learn
     * from the world.  It requires a reasonable amount of time to have passed
     * @param currTime Time stamp of our most reading position reading
     * @param lastPos Previous position reading
     * @param lastTime
     * @return
     */
    public boolean estimatePhysics(double currTime, Point3D lastPos, double lastTime)
    {
    	final double EPSILON = 0.001;
    	boolean updated = false;
    	double deltaTime = currTime - lastTime;
    	if (deltaTime < EPSILON)
    	{
    		return updated; // Can't update estimates
    	}
    	updated = true;
    	Point3D oldVelocity = estimateVelocity(lastPos, deltaTime);
    	if (oldVelocity != null)
    	{
    		Point3D oldAcceleration = estimateAcceleration(oldVelocity, deltaTime);
    	}
    	return updated;
    }
    
    /** This method attempts to estimate the velocity given all the information
     * we have.
     * @param lastPos The last known position
     * @param deltaTime The time between the readings
     * @return The previous velocity (For use in future estimates)
     */
    public Point3D estimateVelocity( Point3D lastPos, double deltaTime)
    {
    	Point3D oldVelocity = estimatedVelocity.copy();
    	estimatedVelocity.m_x = (actualPosition.m_x - lastPos.m_x) / deltaTime;
    	estimatedVelocity.m_y = (actualPosition.m_y - lastPos.m_y) / deltaTime;
    	estimatedVelocity.m_z = (actualPosition.m_z - lastPos.m_z) / deltaTime;
    	double newVel = estimatedVelocity.length();
    	double oldVel = oldVelocity.length();
    	double deltaPos = actualPosition.distanceXY(lastPos);
    	return oldVelocity;
    }
    
    public Point3D estimateAcceleration(Point3D oldVelocity, double deltaTime)
    {
    	Point3D oldAcceleration = estimatedAcceleration.copy();
    	estimatedAcceleration.m_x = (estimatedVelocity.m_x - oldVelocity.m_x) / deltaTime;
    	estimatedAcceleration.m_y = (estimatedVelocity.m_y - oldVelocity.m_y) / deltaTime;
    	estimatedAcceleration.m_z = (estimatedVelocity.m_z - oldVelocity.m_z) / deltaTime;
    	return oldAcceleration;
    }
    
    public void controlTheShip()
    {
    	/* boolean headingOK = adjustHeading();
    	if (headingOK)
    	{
    		// Work on approaching target
    		double distance = actualPosition.distanceXY(currentDestination);
    		if (distance > 325.0)
    		{
    			distance = 325.0; // 325 meters or more causes maximum tilt
    		}
    		if (distance < 25.0) // Last 25 meters, slow down
    		{
    			slowDown();
    		}
    		double myVelocity = estimatedVelocity.length();
    		// Limit how fast we'll go!
    		if (myVelocity > 10.0)
    		{
    			setDesiredTilt(0.0);
    		}
    		else
    		{
    			setDesiredTilt((distance - 25.0) / 300.0 * 10.0);
    		}
    	}
    	else
    	{
    		// Don't keep accelerating wrong direction
    		slowDown();
    	} */
    	selectDesiredAltitude();
		controlAltitude();
    }
    
    public void slowDown()
    { // Warning, this method assumes chopper is moving forward! -- it will speed up if chopper's going backward
    	double realSpeed = estimatedVelocity.length();
    	double mySpeed = realSpeed;
    	if (mySpeed > 20.0)
    	{
    		mySpeed = 20.0;
    	}
    	else if (mySpeed < -20.0)
    	{
    		mySpeed = -20.0;
    	}
    	setDesiredTilt(-mySpeed / 2.0);
    }
    
    public void controlAltitude()
    {
    	if (estimatedAcceleration == null)
    	{
    		return; // can't continue if we don't know
    	}
    	double targetVerticalAcceleration = 0.0;
    	double targetVerticalVelocity = 0.0;
    	if (actualPosition.m_z < desiredAltitude)
    	{
    		targetVerticalVelocity = 1.0;
    		if (estimatedVelocity.m_z < targetVerticalVelocity)
    		{
    			double velocityProportion = (targetVerticalVelocity - estimatedVelocity.m_z) / targetVerticalVelocity;
    			targetVerticalAcceleration = 0.15 * velocityProportion;
    		}
    		else
    		{
    			targetVerticalAcceleration = 0.0;
    		}
    	}
    	if (actualPosition.m_z > desiredAltitude)
    	{
    		targetVerticalVelocity = -1.0;
    		if (estimatedVelocity.m_z > targetVerticalVelocity)
    		{
    			double velocityProportion = (targetVerticalVelocity - estimatedVelocity.m_z) / targetVerticalVelocity;
    			targetVerticalAcceleration = -0.15 * velocityProportion;
    		}
    		else
    		{
    			targetVerticalAcceleration = 0.0;
    		}
    	}
    	double deltaAcceleration = targetVerticalAcceleration - estimatedAcceleration.m_z;
    	if (!(Math.abs(deltaAcceleration) > 10.0))
    	{
    		desMainRotorSpeed_RPM += deltaAcceleration * VERT_CONTROL_FACTOR;
    		myWorld.requestSettings(myChopper.getId(), desMainRotorSpeed_RPM, desTilt_Degrees, desTailRotorSpeed_RPM);
    		System.out.println("DC:Want Alt: " + desiredAltitude + ", Act Alt: " + actualPosition.m_z + ", target accel: "
    				+ targetVerticalAcceleration + ", Actual: " + estimatedAcceleration.m_z + ", Target Rotor Sped: "
    				+ desMainRotorSpeed_RPM);
    	}
    }
    
    public boolean adjustHeading()
    {
    	boolean headingOK = false;
    	if (currentDestination == null)
    	{
    		return headingOK;
    	}
    	Point3D transformation = myWorld.transformations(myChopper.getId());
    	if (transformation == null)
    	{
    		return headingOK;
    	}
    	double actHeading = transformation.m_x;
    	double deltaY = currentDestination.m_y - actualPosition.m_y;
    	double deltaX = currentDestination.m_x - actualPosition.m_x;
    	double desiredHeading = Math.toDegrees(Math.atan2(deltaY,deltaX));
    	if (desiredHeading < 0.0) // NOTE, returns -180 to +180
    	{
    		desiredHeading += 360.0;
    	}
    	double deltaHeading = desiredHeading - actHeading;
    	if (deltaHeading < -180.0)
    	{
    		deltaHeading += 360.0;
    	}
    	else if (deltaHeading > 180.0)
    	{
    		deltaHeading -= 360.0;
    	}
    	if (Math.abs(deltaHeading) < 0.1)
    	{
    		desTailRotorSpeed_RPM = 100.0;
    		// TODO: Future optimization -- don't do this every tick?
    		myWorld.requestSettings(myChopper.getId(), desMainRotorSpeed_RPM, desTilt_Degrees, desTailRotorSpeed_RPM);
    		headingOK = true;
    	}
    	else
    	{
    		// Anything over 30 degrees off gets max rotor speed
    		double deltaRotor = (deltaHeading / 30.0) * 20.0;
    		if (deltaRotor > 20.0)
    		{
    			deltaRotor = 20.0;
    		}
    		else if (deltaRotor < -20.0)
    		{
    			deltaRotor = -20.0;
    		}
    		desTailRotorSpeed_RPM = 100.0 + deltaRotor;
    		myWorld.requestSettings(myChopper.getId(), desMainRotorSpeed_RPM, desTilt_Degrees, desTailRotorSpeed_RPM);
    	}
    	return headingOK;
    }
    
    public void selectDesiredAltitude()
    {
    	if (currentDestination != null)
    	{
    		if (actualPosition.distanceXY(currentDestination) > 10.0)
    		{
    			desiredAltitude = 125.0; // High enough to clear buildings
    		}
    		else
    		{
    			desiredAltitude = 0.1;
    		}
    	}
    	else
    	{
    		//desiredAltitude = 50.0 + 10.0 * (myWorld.getTimestamp() / 100.0);
    		desiredAltitude = 25.0;
    	}
    }
    synchronized public Point3D findClosestDestination()
    {
    	Point3D resultPoint = null;
    	/*
    	ArrayList<Point3D> targetWaypoints = myChopper.getWaypoints();
    	double minDistance = 10000.0;
    	for(Point3D testPoint: targetWaypoints)
    	{
    		double curDistance = actualPosition.distanceXY(testPoint);
    		if (curDistance < minDistance)
    		{
    			resultPoint = testPoint;
    			minDistance = curDistance;
    		}
    	} */
    	resultPoint = actualPosition;
    	return resultPoint;
    }
    
    synchronized public void setDesiredRotorSpeed(double newSpeed)
    {
    	desMainRotorSpeed_RPM = newSpeed;
        myWorld.requestSettings(myChopper.getId(),desMainRotorSpeed_RPM,desTilt_Degrees,desTailRotorSpeed_RPM);
    }
    
    synchronized public void setDesiredTailRotorSpeed(double newSpeed)
    {
    	desTailRotorSpeed_RPM = newSpeed;
        myWorld.requestSettings(myChopper.getId(),desMainRotorSpeed_RPM,desTilt_Degrees,desTailRotorSpeed_RPM);
    }
    
    synchronized public void setDesiredTilt(double newTilt)
    {
    	desTilt_Degrees = newTilt;
        myWorld.requestSettings(myChopper.getId(),desMainRotorSpeed_RPM,desTilt_Degrees,desTailRotorSpeed_RPM);
    }

}
