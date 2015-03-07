package org.heli;

import java.util.ArrayList;

import javax.media.opengl.GL2;
import javax.media.opengl.GLAutoDrawable;

/** This class represents our chopper and its capabilities
 *  Derive fromt this class if you want special features.
 * @author Daniel LaFuze
 * Copyright 2015
 * All Rights Reserved
 *
 */
public class StigChopper {
	
	protected Point3D size;
	
	protected World world;
	
	protected int id;
	
	protected int inventory;
	
	protected static final double X_SIZE = 2.0;
	protected static final double Y_SIZE = 5.0;
	protected static final double Z_SIZE = 3.0;
	
	protected double cargoCapacity; // kg
	
	protected double fuelCapacity; // kg

	protected boolean landed;
	
	// This is the chopper's home base.  For now, it is defined
	// as the location at which it appeared in the world.
	protected Point3D homeBase;
	
	protected ArrayList<Point3D> targetWaypoints;
	
	// Complication -- homeBase isn't known yet -- we need chopperInfo constructed first
	public StigChopper(int chopperID, World theWorld)
	{
		id = chopperID;
		world = theWorld;
		cargoCapacity = ChopperAggregator.TOTAL_CAPACITY / 2.0;
		inventory = (int)Math.round(cargoCapacity / ChopperAggregator.ITEM_WEIGHT);
		fuelCapacity = ChopperAggregator.TOTAL_CAPACITY / 2.0;
		size = new Point3D(X_SIZE, Y_SIZE, Z_SIZE);
		landed = true;
		homeBase = null;
		targetWaypoints = new ArrayList<Point3D>();
				
		System.out.println("StigChopper " + id + " created -- fuel capacity: " + fuelCapacity);
	}
	
	/** This method sets the chopper's waypoints.  Eventually, we will deliver
	 * packages by reaching a waypoint, and notifying the world of our intent
	 * to drop off a package.  Land at a waypoint to enable delivery.
	 * @param newWaypoints
	 */
	public void setWaypoints(ArrayList<Point3D> newWaypoints)
	{
		targetWaypoints = newWaypoints;
	}
	
	public double fuelCapacity()
	{
		return fuelCapacity;
	}
	
	public int itemCount()
	{
		return inventory;
	}
	
	public int getId()
	{
	    return id;
	}
	
	public Point3D getSize()
	{
		Point3D result = new Point3D(X_SIZE, Y_SIZE, Z_SIZE);
		return result;
	}
	
	
	/** This method renders a chopper.  We'll get the position from the world.
	 * We need to get information about the chopper's orientation from the
	 * world object that is in charge of the choppers Orientation.
	 * @param drawable Access to OpenGL pipeline
	 * @param actHeading Direction in degrees, so we can rotate appropriately
	 * @param actTilt Tilt in degrees so we can rotate accordingly
	 * @param rotorPos Rotation of the rotor (0 - 360) so we can draw it
	 * @param tailRotorPos Rotation of the rotor (0 - 360) so we can draw it
	 */
	public void render(GLAutoDrawable drawable, double actHeading, double actTilt, double rotorPos, double tailRotorPos)
	{
        GL2 gl = drawable.getGL().getGL2();
        Point3D myPosition = world.gps(id);
        // Capture our first position reading as our home base
        if (homeBase == null)
        {
        	homeBase = myPosition;
        }
        // This method returns the bottom center of our chopper, first, get center
        Point3D centerPos = new Point3D(myPosition.m_x, myPosition.m_y, myPosition.m_z);
        // For now, we need our center point for an axis of rotation (Pitch and heading)
        // When we start rendering a more realistic chopper, we'll have to do that in addition
        // to rotating the rotors
        centerPos.m_z += Z_SIZE / 2.0;
        // Next, get bounding rectangular prism
        myPosition.m_x -= X_SIZE / 2.0;
        myPosition.m_y -= Y_SIZE / 2.0;
        Point3D mySize = new Point3D(X_SIZE, Y_SIZE, Z_SIZE);
        // Translate the center of chopper to the origin, so rotation doesn't move chopper
        gl.glPushMatrix();
        gl.glTranslated(centerPos.m_x, centerPos.m_y, centerPos.m_z);
        Point3D transformation = world.transformations(id);
        // rotate chopper by heading
        gl.glRotated(transformation.m_x, 0.0, 0.0, 1.0);
        // rotate chopper by tilt
        gl.glRotated(transformation.m_y, 1.0, 0.0, 0.0);
        gl.glTranslated(-centerPos.m_x,  -centerPos.m_y, -centerPos.m_z);
        ArrayList<Object3D> chopperObjects = makeChopperObjects(myPosition, mySize);
        for (Object3D chopperObject : chopperObjects)
        {
	        chopperObject.setColor(1.0 - 0.25 * id,  0.0, 0.0 + 0.25 * id, 1.0);
			double objColor[] = chopperObject.getColor();
			float[] bufferArray = World.makeVertexArray(chopperObject.getPosition(), chopperObject.getSize());
			if (bufferArray != null)
			{
				gl.glColor4dv(objColor, 0);
				World.drawRectangles(gl,bufferArray, true);
			}
			gl.glColor4dv(objColor, 0);
        }
        drawTopRotorPyramid(gl, centerPos.copy());
        //drawWindows(gl, centerPos.copy());
        drawRearFrame(gl, centerPos.copy());
        drawTopRotor(gl, centerPos.copy(), rotorPos);
        drawTailRotor(gl, centerPos.copy(), tailRotorPos, 0.3);
        drawTailRotor(gl, centerPos.copy(), tailRotorPos, -0.3);
        gl.glPopMatrix();
	}
	
	private void drawWindows(GL2 gl, Point3D centerPos)
	{
		gl.glColor4d(0.20, 0.2, 0.2, 0.2);
		gl.glBegin(gl.GL_TRIANGLES);
		// Draw Left Top Angled Window
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.5, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x - 1.0, centerPos.m_y - 2.0, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.0, centerPos.m_z + 1.0);
		// Draw Right Top Angled Window
		gl.glVertex3d(centerPos.m_x + 1.0, centerPos.m_y - 2.0, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.5, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.0, centerPos.m_z + 1.0);
		gl.glEnd();
		// Draw Front Top Straight Window
		gl.glBegin(gl.GL_QUADS);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.5, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.5, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.0, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.0, centerPos.m_z + 1.0);
		gl.glEnd();
		gl.glBegin(gl.GL_TRIANGLES);
		// Draw Left Bottom Angled Window
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.5, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x - 1.0, centerPos.m_y - 2.0, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.0, centerPos.m_z - 1.0);
		// Draw Right Bottom Angled Window
		gl.glVertex3d(centerPos.m_x + 1.0, centerPos.m_y - 2.0, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.5, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.0, centerPos.m_z - 1.0);
		gl.glEnd();
		// Draw Front Bottom Straight Window
		gl.glBegin(gl.GL_QUADS);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.0, centerPos.m_z - 1.0);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.0, centerPos.m_z - 1.0);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.5, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.5, centerPos.m_z - 0.5);
		// Draw Left Straight Window
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.5, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.5, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.0, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 2.0, centerPos.m_z + 0.5);
		// Draw Right Straight Window
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.0, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.0, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.5, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 2.5, centerPos.m_z + 0.5);
		gl.glEnd();
	}
	
	private void drawTopRotorPyramid(GL2 gl, Point3D centerPos)
	{
		gl.glBegin(gl.GL_TRIANGLE_STRIP);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 1.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 0.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x, centerPos.m_y - 1.25, centerPos.m_z + 1.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 0.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 1.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 1.75, centerPos.m_z + 1.0);
		gl.glEnd();
		gl.glBegin(gl.GL_LINES);
		gl.glColor3d(0.25, 0.25, 0.25);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 1.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 0.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x, centerPos.m_y - 1.25, centerPos.m_z + 1.5);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 0.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 0.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x, centerPos.m_y - 1.25, centerPos.m_z + 1.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 0.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 1.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x, centerPos.m_y - 1.25, centerPos.m_z + 1.5);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y - 1.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y - 1.75, centerPos.m_z + 1.0);
		gl.glVertex3d(centerPos.m_x, centerPos.m_y - 1.25, centerPos.m_z + 1.5);
		gl.glEnd();
	}
	
	private void drawRearFrame(GL2 gl, Point3D centerPos)
	{
		gl.glBegin(gl.GL_LINES);
		gl.glColor3d(0.75, 0.75, 0.75);
		// Draw 4 lines to contain the frame
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x - 0.25, centerPos.m_y + 1.5, centerPos.m_z + 0.25);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x + 0.25, centerPos.m_y + 1.5, centerPos.m_z + 0.25);
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x - 0.25, centerPos.m_y + 1.5, centerPos.m_z - 0.25);
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x + 0.25, centerPos.m_y + 1.5, centerPos.m_z - 0.25);
		// Draw left X closest to body
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z - 0.5 + (0.25*0.33));
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z + 0.5 - (0.25*0.33));
		// Draw Right X closest to body
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z - 0.5 + (0.25*0.33));
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z + 0.5 - (0.25*0.33));
		// Draw Top X closest to body
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z + 0.5 - (0.25*0.33));
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y, centerPos.m_z + 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z + 0.5 - (0.25*0.33));
		// Draw Bottom X closest to body
		gl.glVertex3d(centerPos.m_x - 0.5, centerPos.m_y, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z - 0.5 + (0.25*0.33));
		gl.glVertex3d(centerPos.m_x + 0.5, centerPos.m_y, centerPos.m_z - 0.5);
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z - 0.5 + (0.25*0.33));
		// Draw second left X
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z + 0.5 - (0.25*0.66));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z - 0.5 + (0.25*0.33));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z - 0.5 + (0.25*0.66));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z + 0.5 - (0.25*0.33));
		// Draw second Right X
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z + 0.5 - (0.25*0.66));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z - 0.5 + (0.25*0.33));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.33), centerPos.m_y + 0.5, centerPos.m_z - 0.5 + (0.25*0.66));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z + 0.5 - (0.25*0.33));
		// Draw second Top X
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.66), centerPos.m_y + 0.5, centerPos.m_z + 0.5 - (0.25*0.33));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.33), centerPos.m_y + 1.0, centerPos.m_z + 0.5 - (0.25*0.66));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.66), centerPos.m_y + 0.5, centerPos.m_z + 0.5 - (0.25*0.33));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.33), centerPos.m_y + 1.0, centerPos.m_z + 0.5 - (0.25*0.66));
		// Draw second Bottom X
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*1.0), centerPos.m_y + 0.5, centerPos.m_z - 0.5 + (0.25*0.66));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z - 0.5 + (0.25*1.0));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*1.0), centerPos.m_y + 0.5, centerPos.m_z - 0.5 + (0.25*0.66));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z - 0.5 + (0.25*1.0));
		// Draw third left X
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z + 0.5 - (0.25*1.0));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*1.0), centerPos.m_y + 1.5, centerPos.m_z - 0.5 + (0.25*0.66));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z - 0.5 + (0.25*1.0));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*1.0), centerPos.m_y + 1.5, centerPos.m_z + 0.5 - (0.25*0.66));
		// Draw third Right X
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z + 0.5 - (0.25*1.0));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*1.0), centerPos.m_y + 1.5, centerPos.m_z - 0.5 + (0.25*0.66));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.66), centerPos.m_y + 1.0, centerPos.m_z - 0.5 + (0.25*1.0));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*1.0), centerPos.m_y + 1.5, centerPos.m_z + 0.5 - (0.25*0.66));
		// Draw third Top X
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*1.0), centerPos.m_y + 1.0, centerPos.m_z + 0.5 - (0.25*0.66));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.66), centerPos.m_y + 1.5, centerPos.m_z + 0.5 - (0.25*1.0));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*1.0), centerPos.m_y + 1.0, centerPos.m_z + 0.5 - (0.25*0.66));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.66), centerPos.m_y + 1.5, centerPos.m_z + 0.5 - (0.25*1.0));
		// Draw third Bottom X
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*1.0), centerPos.m_y + 1.0, centerPos.m_z - 0.5 + (0.25*0.66));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*0.66), centerPos.m_y + 1.5, centerPos.m_z - 0.5 + (0.25*1.0));
		gl.glVertex3d(centerPos.m_x + 0.5 - (0.25*1.0), centerPos.m_y + 1.0, centerPos.m_z - 0.5 + (0.25*0.66));
		gl.glVertex3d(centerPos.m_x - 0.5 + (0.25*0.66), centerPos.m_y + 1.5, centerPos.m_z - 0.5 + (0.25*1.0));		
		gl.glEnd();
	}
	
	private void drawTopRotor(GL2 gl, Point3D centerPos, double rotorPos)
	{
		// Move center to center of top rotor
		centerPos.m_y -= 1.25;
    	centerPos.m_z += 1.50;
    	gl.glPushMatrix();
    	gl.glTranslated(centerPos.m_x, centerPos.m_y, centerPos.m_z);
    	gl.glRotated(rotorPos, 0.0, 0.0, 1.0);
    	gl.glTranslated(-centerPos.m_x, -centerPos.m_y, -centerPos.m_z);
    	// Draw main rotor
    	gl.glBegin(gl.GL_LINES);
    	gl.glColor3d(1.0, 1.0, 0.00);
    	// All 3 rotor blades start in the center
    	gl.glVertex3d(centerPos.m_x, centerPos.m_y, centerPos.m_z);
    	gl.glVertex3d(centerPos.m_x, centerPos.m_y + 1.5, centerPos.m_z);
    	gl.glVertex3d(centerPos.m_x, centerPos.m_y, centerPos.m_z);
    	gl.glVertex3d(centerPos.m_x - 1.3, centerPos.m_y - 1.0, centerPos.m_z);
    	gl.glVertex3d(centerPos.m_x, centerPos.m_y, centerPos.m_z);
    	gl.glVertex3d(centerPos.m_x + 1.3, centerPos.m_y - 1.0, centerPos.m_z);
    	gl.glEnd();
    	gl.glPopMatrix();
	}
	
	private void drawTailRotor(GL2 gl, Point3D centerPos, double rotorPos, double xOffset)
	{
		// Move center to center of top rotor
    	centerPos.m_y += 2.00;
    	centerPos.m_x += xOffset;
    	gl.glPushMatrix();
    	gl.glTranslated(centerPos.m_x, centerPos.m_y, centerPos.m_z);
    	gl.glRotated(rotorPos, 1.0, 0.0, 0.0);
    	gl.glTranslated(-centerPos.m_x, -centerPos.m_y, -centerPos.m_z);
    	// Draw tail rotor
    	gl.glBegin(gl.GL_LINES);
    	gl.glColor3d(1.0, 1.0, 0.0);
    	// Both rotor blades start in the center
    	gl.glVertex3d(centerPos.m_x, centerPos.m_y, centerPos.m_z);
    	gl.glVertex3d(centerPos.m_x, centerPos.m_y, centerPos.m_z + 0.5);
    	gl.glVertex3d(centerPos.m_x, centerPos.m_y, centerPos.m_z);
    	gl.glVertex3d(centerPos.m_x, centerPos.m_y, centerPos.m_z - 0.5);
    	gl.glEnd();
    	gl.glPopMatrix();
	}
	
	private ArrayList<Object3D> makeChopperObjects(Point3D myPos, Point3D mySize)
	{
		ArrayList<Object3D> resultObjects = new ArrayList<Object3D>();
		Point3D firstPoint = new Point3D(myPos.m_x + 0.5, myPos.m_y, myPos.m_z + 1.0);
		Point3D firstSize = new Point3D(1.0, 2.5, 1.0);
		Object3D firstObj = new Object3D(firstPoint, firstSize);
		resultObjects.add(firstObj);
		Point3D secondPoint = new Point3D(myPos.m_x, myPos.m_y + 0.5, myPos.m_z + 0.5);
		Point3D secondSize = new Point3D(2.0, 1.5, 2.0);
		Object3D secondObj = new Object3D(secondPoint, secondSize);
		resultObjects.add(secondObj);
		Point3D firstTPoint = new Point3D(myPos.m_x + 0.75, myPos.m_y + 4.0, myPos.m_z + 1.25);
		Point3D firstTSize = new Point3D(0.5, 1.0, 0.5);
		Object3D firstTObj = new Object3D(firstTPoint, firstTSize);
		resultObjects.add(firstTObj);
		Point3D secondTPoint = new Point3D(myPos.m_x + 0.75, myPos.m_y + 4.25, myPos.m_z + 1.0);
		Point3D secondTSize = new Point3D(0.5, 0.5, 1.0);
		Object3D secondTObj = new Object3D(secondTPoint, secondTSize);
		resultObjects.add(secondTObj);
		return resultObjects;
	}
}
