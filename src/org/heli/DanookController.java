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
	private static final int APPROACHING_TARGET_ROUGH = 2;
	private static final int TURN_TOWARD = 3;
	private static final int SLOWING = 4;
	private static final int FINE_TUNE_HEADING = 5;
	private static final int APPROACHING_TARGET_FINE = 6;
	private static final int DESCENDING = 7;
	
	private static final double VERT_CONTROL_FACTOR = 3.0;
	
	private static final double MAX_VERT_VELOCITY = 2.5;
	
	private static final double MAX_HORZ_VELOCITY = 10.0;
	
	private static final double MAX_VERT_ACCEL = 0.5;
	
	private static final double DECEL_DISTANCE = 10.0;
	
	private static final double DECEL_SPEED = 0.5;
	
	private Danook myChopper;
	private World myWorld;
	private int myState = STATE_LANDED;
	private int stateCounter = 0;
	
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
    	estimatedVelocity.m_x = (actualPosition.m_x - lastPos.m_x) / deltaTime;
    	estimatedVelocity.m_y = (actualPosition.m_y - lastPos.m_y) / deltaTime;
    	estimatedVelocity.m_z = (actualPosition.m_z - lastPos.m_z) / deltaTime;
    	double newVel = estimatedVelocity.length();
    	double oldVel = oldVelocity.length();
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
    	++stateCounter;
    	switch(myState)
    	{
    	case FINDING_HEADING:
    	{
    		boolean headingOK = adjustHeading(false);
    		if (headingOK)
    		{
    			nextState = APPROACHING_TARGET_ROUGH;
    		}
    		if (stateCounter > 500)
    		{
    			nextState = TURN_TOWARD;
    		}
    		break;
    	}
    	case APPROACHING_TARGET_ROUGH:
    	{
    		double distance = actualPosition.distanceXY(currentDestination);
    		World.dbg(TAG,"Approaching? " + distance,DC_DBG);
    		if (distance > 25.0)
    		{
    			approachTarget(true);
    		}
    		else
    		{
    			nextState = TURN_TOWARD;
    		}
    		if (stateCounter > 500)
    		{
    			nextState = FINDING_HEADING;
    		}
    		break;
    	}
    	case TURN_TOWARD:
    	{
    		boolean turnComplete = adjustHeading(true);
    		if (turnComplete)
    		{
    			nextState = SLOWING;
    		}
    		break;
    	}
    	case SLOWING:
    	{
    		boolean stopped = slowDown();
    		double distance = actualPosition.distanceXY(currentDestination);
    		if (stopped)
    		{
    			if (distance < 25.0)
    			{
        			nextState = FINE_TUNE_HEADING;
    			}
    			else
    			{
    				nextState = FINDING_HEADING;
    			}
    		}
    		break;
    	}
    	case DanookController.FINE_TUNE_HEADING:
    	{
    		boolean headingOK = adjustHeading(false);
    		if (headingOK)
    		{
    			nextState = APPROACHING_TARGET_FINE;
    		}
    		break;
    	}
    	case APPROACHING_TARGET_FINE:
    	{
    		boolean headingOK = adjustHeading(false);
    		double distance = actualPosition.distanceXY(currentDestination);
    		if (distance > 25.0)
    		{
    			nextState = APPROACHING_TARGET_ROUGH;
    		}
    		else if (distance > 1.0)
    		{
    			approachTarget(false);
    		}
    		else
    		{
    			nextState = DESCENDING;
    		}
    		break;
    	}
    	}
		//World.dbg(TAG,"Old State: " + myState + ", New State: " + nextState + ", state counter: " + stateCounter,DC_DBG);
		if (nextState != myState)
		{
			stateCounter = 0;
		}
    	myState = nextState;
    	selectDesiredAltitude();
		myState = controlAltitude(myState);
    }
    
    public void approachTarget(boolean highSpeedOK)
    {
		// Work on approaching target
		double distance = actualPosition.distanceXY(currentDestination);
		double maxVelocity = 0.5;
		if (highSpeedOK)
		{
			maxVelocity = 5.0;
			if (distance > 525.0)
			{
				distance = 525.0; // 525 meters or more causes maximum tilt
			}
		}
		Point3D zeroVelocity = new Point3D(0.0, 0.0, 0.0);
		double lateralVelocity = estimatedVelocity.distanceXY(zeroVelocity);
		// Limit how fast we'll go!
		if (lateralVelocity > maxVelocity)
		{
			setDesiredTilt(0.0);
		}
		else if (highSpeedOK)
		{
			setDesiredTilt((distance - 25.0) / 500.0 * 10.0);
		}
		else
		{
			setDesiredTilt(0.1);
		}
    	Point3D transformation = myWorld.transformations(myChopper.getId());
    	double heading = 0.0;
    	if (transformation != null)
    	{
    		heading = transformation.m_x;
    	}
		int msTime = (int)Math.floor(myWorld.getTimestamp() * 1000);
		long deltaX_mm = (long)Math.floor((actualPosition.m_x - currentDestination.m_x) * 1000);
		long deltaY_mm = (long)Math.floor((actualPosition.m_y - currentDestination.m_y) * 1000);
		long actVelX_mm = (long)Math.floor(estimatedVelocity.m_x * 1000);
		long actVelY_mm = (long)Math.floor(estimatedVelocity.m_y * 1000);
		/* World.dbg(TAG,"Time: " + msTime + ", Delta mm: (" + deltaX_mm + ", " + deltaY_mm + "), velocity mm: ("
		+ actVelX_mm + ", " + actVelY_mm + "), heading: " + heading,DC_DBG); */
    }
    
    public boolean slowDown()
    {
    	boolean allStopped = false;
    	boolean movingForward = false;
    	Point3D transformation = myWorld.transformations(myChopper.getId());
    	if (transformation == null)
    	{
    		return allStopped; // Can't do anything
    	}
    	double actHeading = transformation.m_x;

    	if (actHeading >= 0 && actHeading < 90.0) // Q1
    	{
    		if (estimatedVelocity.m_x >= 0 && estimatedVelocity.m_y >= 0)
    		{
    			movingForward = true;
    		}
    	}
    	else if (actHeading >= 90 && actHeading < 180.0) // Q2
    	{
    		if (estimatedVelocity.m_x >= 0 && estimatedVelocity.m_y <= 0)
    		{
    			movingForward = true;
    		}
    	}
    	else if (actHeading >= 180 && actHeading < 270.0) // Q3
    	{
    		if (estimatedVelocity.m_x <= 0 && estimatedVelocity.m_y <= 0)
    		{
    			movingForward = true;
    		}
    	}
    	else if (actHeading >= 270 && actHeading < 360.0) // Q3
    	{
    		if (estimatedVelocity.m_x <= 0 && estimatedVelocity.m_y >= 0)
    		{
    			movingForward = true;
    		}
    	}

    	Point3D zeroVelocity = new Point3D(0.0, 0.0, 0.0);
    	double realSpeed = estimatedVelocity.distanceXY(zeroVelocity);
    	double mySpeed = realSpeed;
    	if (mySpeed > 40.0)
    	{
    		mySpeed = 40.0;
    	}
    	if (!movingForward)
    	{
    		mySpeed *= -1.0;
    	}
    	setDesiredTilt(-mySpeed / 4.0);
		int msTime = (int)Math.floor(myWorld.getTimestamp() * 1000);
		long deltaX_mm = (long)Math.floor((actualPosition.m_x - currentDestination.m_x) * 1000);
		long deltaY_mm = (long)Math.floor((actualPosition.m_y - currentDestination.m_y) * 1000);
		long actVelX_mm = (long)Math.floor(estimatedVelocity.m_x * 1000);
		long actVelY_mm = (long)Math.floor(estimatedVelocity.m_y * 1000);
		// TODO: May need to ignore vertical velocity considered elsewhere
		if (estimatedVelocity.length() < 0.25)
		{
			allStopped = true;
		}
		//World.dbg(TAG,"Time: " + msTime + ", Slowing Down fwd? " + movingForward + ", want tilt: " + desTilt_Degrees,DC_DBG);
		return allStopped;
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
    	double targetVerticalVelocity = computeDesiredVelocity(actualPosition.m_z,desiredAltitude);
    	double deltaVelocity = targetVerticalVelocity - estimatedVelocity.m_z;
    	double targetVerticalAcceleration = computeDesiredAcceleration(estimatedVelocity.m_z, targetVerticalVelocity);
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
    	int msTime = (int)Math.floor(myWorld.getTimestamp() * 1000);
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
    
    public double computeDesiredVelocity(double actAlt, double desAlt)
    {
    	double targetVelocity = MAX_VERT_VELOCITY;
    	double deltaValue = Math.abs(desAlt - actAlt);
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
    
    public double computeDesiredAcceleration(double actVel, double desVel)
    {
    	double targetAccel = MAX_VERT_ACCEL;
    	double deltaValue = Math.abs(desVel - actVel);
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
		/* World.dbg(TAG,"Time: " + msTime + ", Want Pos (" + currentDestination.m_x + ", " + currentDestination.m_y + 
		") Act Pos (" + actualPosition.m_x + ", " + actualPosition.m_y + ") desired: " + desiredHeading,DC_DBG); */
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
