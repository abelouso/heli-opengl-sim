/** Copyright 2015, Sasha and Dan
 * 
 */
package org.heli;

import java.util.ArrayList;

import javax.media.opengl.GLAutoDrawable;

/** This class will control a Danook Helicopter
 * 
 * @author Daniel
 *
 */
public class DanookController extends Thread
{
	// TODO: Implement a state machine
    public static final String TAG = "DC:";
    public static final long DC_DBG = 0x2;
	private static final int STATE_LANDED = 0;
	private static final int FINDING_HEADING = 1;
	private static final int APPROACHING = 2;
	private static final int STOPPING = 3;
	private static final int DESCENDING = 4;
	
	private static final double VERT_CONTROL_FACTOR = 3.0;
	private static final double HORZ_CONTROL_FACTOR = 0.15;
	
	private static final double MAX_VERT_VELOCITY = 2.5;
	
	private static final double MAX_HORZ_VELOCITY = 5.0;
	
	private static final double MAX_VERT_ACCEL = 0.5;
	
	private static final double MAX_HORZ_ACCEL = 1.0;
	
	private static final double DECEL_DISTANCE_VERT = 10.0;
	
	private static final double DECEL_DISTANCE_HORZ = 20.0;

	private static final double VERT_DECEL_SPEED = 0.5;
	
	private static final double HORZ_DECEL_SPEED = 2.0;
	
	private Danook myChopper;
	private World myWorld;
	private int myState = STATE_LANDED;
	
    private double desMainRotorSpeed_RPM = 0.0;
    private double desTailRotorSpeed_RPM = 0.0;
    private double desTilt_Degrees = 0.0;
    
    private Point3D estimatedAcceleration;
    private Point3D estimatedVelocity;
    private Point3D actualPosition;
    
    public double desiredHeading;
    public double desiredAltitude;
    
    private double lastDistance;
    
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
        lastDistance = 0.0;
        
        currentDestination = null;
	}

	public Point3D getDestination()
	{
		if (currentDestination != null)
		{
			return currentDestination.copy();
		}
		else
		{
			return currentDestination;
		}
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
			World.dbg(TAG,"Caught an exception",DC_DBG);
		}
		Point3D lastPosition = null;
		double currTime = 0.0;
		double lastTime = 0.0;
		double worldDivider = myWorld.timeRatio();
		long deltaTime = Math.round(20.0 / worldDivider);
    	while (true)
    	{
    		try
    		{
    			// Do smart stuff...
    			Thread.sleep(deltaTime);
    			synchronized(myWorld)
    			{
    				actualPosition = myWorld.gps(myChopper.getId());
    			}
    			currTime = actualPosition.t();
    			if (currentDestination == null)
    			{
    				currentDestination = findClosestDestination();
    				World.dbg(TAG,"Got a destination: " + currentDestination.info(),DC_DBG);
    			}
    			else
    			{
    				// TODO: See if we're on the ground at the destination
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
    					World.dbg(TAG,"DC: No physics estimate?",DC_DBG);
    				}
    			}
    			lastPosition = actualPosition.copy();
    			lastTime = currTime;
    		}
    		catch (Exception e)
    		{
    			World.dbg(TAG,"Caught an exception: " + e.toString(),DC_DBG);
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
    	double realDelta = actualPosition.t() - lastPos.t();
    	estimatedVelocity.m_x = (actualPosition.m_x - lastPos.m_x) / deltaTime;
    	estimatedVelocity.m_y = (actualPosition.m_y - lastPos.m_y) / deltaTime;
    	estimatedVelocity.m_z = (actualPosition.m_z - lastPos.m_z) / deltaTime;
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
    	int nextState = myState;
    	switch(myState)
    	{
    	case FINDING_HEADING:
    	{
    		boolean headingOK = adjustHeading(false);
    		if (headingOK)
    		{
    			// Ensure we run through approaching at least once
    			lastDistance = 9999.9;
    			nextState = APPROACHING;
    		}
    		break;
    	}
    	case APPROACHING:
    	{
    		double distance = actualPosition.distanceXY(currentDestination);
    		if (distance > lastDistance)
    		{
    			nextState = STOPPING; // Don't keep going farther away!
    		}
    		else
    		{
    			boolean success = approachTarget();
    		}
    		break;
    	}
    	case STOPPING:
    	{
    		break;
    	}
    	}
    	myState = nextState;
    	selectDesiredAltitude();
		myState = controlAltitude(myState);
    }
    
    public boolean approachTarget()
    {
    	if (currentDestination == null)
    	{
    		return false;
    	}
    	double distance = actualPosition.distanceXY(currentDestination);
    	double targetLateralVelocity = computeDesiredVelocity(0.0,distance,false);
    	double estimatedLateralVelocity = Math.sqrt(estimatedVelocity.m_x * estimatedVelocity.m_x + estimatedVelocity.m_y * estimatedVelocity.m_y);
    	double deltaVelocity = targetLateralVelocity - estimatedLateralVelocity;
    	double targetLateralAcceleration = computeDesiredAcceleration(estimatedLateralVelocity, targetLateralVelocity,false);
    	double estimatedLateralAcceleration = Math.sqrt(estimatedAcceleration.m_x * estimatedAcceleration.m_x + estimatedAcceleration.m_y * estimatedAcceleration.m_y);
    	double deltaAcceleration = targetLateralAcceleration - estimatedLateralAcceleration;
    	if (deltaAcceleration > MAX_HORZ_ACCEL)
    	{
    		deltaAcceleration = MAX_HORZ_ACCEL;
    	}
    	if (deltaAcceleration < (-MAX_HORZ_ACCEL))
    	{
    		deltaAcceleration = (-MAX_HORZ_ACCEL);
    	}
    	desTilt_Degrees += deltaAcceleration * HORZ_CONTROL_FACTOR;
    	myWorld.requestSettings(myChopper.getId(), desMainRotorSpeed_RPM, desTilt_Degrees, desTailRotorSpeed_RPM);
    	int msTime = (int)Math.floor(myWorld.getTimestamp() * 1000);
    	int desVel = (int)Math.floor(targetLateralVelocity * 1000);
    	int actVel = (int)Math.floor(estimatedLateralVelocity * 1000);
    	int desAcc = (int)Math.floor(targetLateralAcceleration * 1000);
    	int actAcc = (int)Math.floor(estimatedLateralAcceleration * 1000);
    	int distance_mm = (int)Math.floor(distance * 1000);
    	World.dbg(TAG," Time: " + msTime + ", Distance: " + distance_mm + ", actVel: " + actVel + ", desVel: " + desVel + ", actAcc: " +
    			actAcc + ", desired accel: " + desAcc + ", tiltChange: " + (deltaAcceleration * HORZ_CONTROL_FACTOR) + ", new: " + desTilt_Degrees,DC_DBG);
    	return true;
    }
    
    /** Call this method to check if vertical velocity and acceleration are
     * both exactly zero.  The only way that happens is if we're on the ground.
     * @return
     */
    public boolean checkForLanded()
    {
    	boolean onGround = false;
    	final double EPSILON = 0.001;
    	if ((Math.abs(estimatedVelocity.m_z) < EPSILON) &&
    		(Math.abs(estimatedAcceleration.m_z) < EPSILON))
    	{
    		onGround = true;
    	}
    	return onGround;
    }
    
    public int controlAltitude(int inState)
    {
    	int outState = inState;
    	if (estimatedAcceleration == null || estimatedVelocity == null)
    	{
    		return outState; // can't continue if we don't know
    	}
    	boolean onGround = checkForLanded();
    	if (onGround)
    	{
    		if (inState == DESCENDING)
    		{
    			outState = STATE_LANDED;
    		}
    		return outState;
    	}
    	if (inState == STATE_LANDED)
    	{
    		outState = FINDING_HEADING;
    	}
    	double targetVerticalVelocity = computeDesiredVelocity(actualPosition.m_z,desiredAltitude,true);
    	double deltaVelocity = targetVerticalVelocity - estimatedVelocity.m_z;
    	double targetVerticalAcceleration = computeDesiredAcceleration(estimatedVelocity.m_z, targetVerticalVelocity,true);
    	double deltaAcceleration = targetVerticalAcceleration - estimatedAcceleration.m_z;
    	if (deltaAcceleration > MAX_VERT_ACCEL)
    	{
    		deltaAcceleration = MAX_VERT_ACCEL;
    	}
    	if (deltaAcceleration < (-MAX_VERT_ACCEL))
    	{
    		deltaAcceleration = (-MAX_VERT_ACCEL);
    	}
    	desMainRotorSpeed_RPM += deltaAcceleration * VERT_CONTROL_FACTOR;
    	int msTime = (int)Math.floor(actualPosition.t() * 1000);
    	int desHeight_mm = (int)Math.floor(desiredAltitude * 1000);
    	int actHeight_mm = (int)Math.floor(actualPosition.m_z * 1000);
    	int desVel = (int)Math.floor(targetVerticalVelocity * 1000);
    	int actVel = (int)Math.floor(estimatedVelocity.m_z * 1000);
    	int desAcc = (int)Math.floor(targetVerticalAcceleration * 1000);
    	int actAcc = (int)Math.floor(estimatedAcceleration.m_z * 1000);
    	myWorld.requestSettings(myChopper.getId(), desMainRotorSpeed_RPM, desTilt_Degrees, desTailRotorSpeed_RPM);
    	/* World.dbg(TAG," Time: " + msTime + ", Want mm: " + desHeight_mm + ", Alt mm: " + actHeight_mm + 
    			", actVel: " + estimatedVelocity.m_z + ", deltaAcc: " +
    			deltaAcceleration + ", desired accel: " + targetVerticalAcceleration,DC_DBG); */
    	return outState;
    }
    
    public double computeDesiredVelocity(double actAlt, double desAlt, boolean doVertical)
    {
    	double targetVelocity = (doVertical?MAX_VERT_VELOCITY:MAX_HORZ_VELOCITY);
    	double deltaValue = Math.abs(desAlt - actAlt);
    	final double DECEL_DISTANCE = (doVertical?DECEL_DISTANCE_VERT:DECEL_DISTANCE_HORZ);
    	if (deltaValue < DECEL_DISTANCE)
    	{
    		targetVelocity = deltaValue / DECEL_DISTANCE;
    	}
    	if (actAlt > desAlt)
    	{
    		targetVelocity *= -1.0;
    	}
    	return targetVelocity;
    }
    
    public double computeDesiredAcceleration(double actVel, double desVel, boolean doVertical)
    {
    	double targetAccel = (doVertical?MAX_VERT_ACCEL:MAX_HORZ_ACCEL);
    	double deltaValue = Math.abs(desVel - actVel);
    	final double DECEL_SPEED = (doVertical?VERT_DECEL_SPEED:HORZ_DECEL_SPEED);
    	if (deltaValue < DECEL_SPEED)
    	{
    		targetAccel = deltaValue / DECEL_SPEED;
    	}
    	if (actVel > desVel)
    	{
    		targetAccel *= -1.0;
    	}
    	return targetAccel;
    }
    
    public boolean adjustHeading(boolean useVelocity)
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
    	if (useVelocity) // Strike that
    	{
    		deltaY = estimatedVelocity.y();
    		deltaX = estimatedVelocity.x();
    	}
    	double desiredHeading = Math.toDegrees(Math.atan2(deltaX,deltaY));
    	if (desiredHeading < 0.0) // NOTE, returns -180 to +180
    	{
    		desiredHeading += 360.0;
    	}
		int msTime = (int)Math.floor(myWorld.getTimestamp() * 1000);
		World.dbg(TAG,"Time: " + msTime + ", Want Pos (" + currentDestination.m_x + ", " + currentDestination.m_y + 
		") Act Pos (" + actualPosition.m_x + ", " + actualPosition.m_y + ") desired: " + desiredHeading + ", actHeading: " + actHeading,DC_DBG);
    	double deltaHeading = desiredHeading - actHeading;
    	if (deltaHeading < -180.0)
    	{
    		deltaHeading += 360.0;
    	}
    	else if (deltaHeading > 180.0)
    	{
    		deltaHeading -= 360.0;
    	}
    	if (Math.abs(deltaHeading) < 0.03)
    	{
    		desTailRotorSpeed_RPM = 100.0;
    		// TODO: Future optimization -- don't do this every tick?
    		myWorld.requestSettings(myChopper.getId(), desMainRotorSpeed_RPM, desTilt_Degrees, desTailRotorSpeed_RPM);
    		headingOK = true;
    	}
    	else
    	{
    		// Anything over 10 degrees off gets max rotor speed
    		double deltaRotor = (deltaHeading / 10.0) * 20.0;
    		if (deltaRotor > 5.0)
    		{
    			deltaRotor = 5.0;
    		}
    		else if (deltaRotor < -5.0)
    		{
    			deltaRotor = -5.0;
    		}
    		desTailRotorSpeed_RPM = ChopperInfo.STABLE_TAIL_ROTOR_SPEED + deltaRotor;
    		myWorld.requestSettings(myChopper.getId(), desMainRotorSpeed_RPM, desTilt_Degrees, desTailRotorSpeed_RPM);
    	}
    	return headingOK;
    }
    
    public void selectDesiredAltitude()
    {
    	if (currentDestination != null)
    	{
    		if (actualPosition.distanceXY(currentDestination) > 5.0)
    		{
    			desiredAltitude = 125.0; // High enough to clear buildings
    			if (myState == DESCENDING)
    			{
    				myState = FINDING_HEADING;
    			}
    		}
    		else
    		{
    			desiredAltitude = 0.1;
    		}
    	}
    	else
    	{
    		desiredAltitude = 2.0 + 98.0 * (Math.floor(myWorld.getTimestamp() / 100.0)%2);
    	}
    }
    synchronized public Point3D findClosestDestination()
    {
    	Point3D resultPoint = null;
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
    	}
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
