package org.heli;

import javax.media.opengl.GL2;
import javax.media.opengl.GLAutoDrawable;

/** This class represents our chopper and its capabilities
 * 
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
	
	public StigChopper(int chopperID, World theWorld) {
		id = chopperID;
		world = theWorld;
		cargoCapacity = ChopperAggregator.TOTAL_CAPACITY / 2.0;
		inventory = (int)Math.round(cargoCapacity / ChopperAggregator.ITEM_WEIGHT);
		fuelCapacity = ChopperAggregator.TOTAL_CAPACITY / 2.0;
		size = new Point3D(X_SIZE, Y_SIZE, Z_SIZE);
		landed = true;
		System.out.println("StigChopper " + id + " created -- fuel capacity: " + fuelCapacity);
	}
	
	public double fuelCapacity() {
		return fuelCapacity;
	}
	
	public int itemCount() {
		return inventory;
	}
	
	public int getId()
	{
	    return id;
	}
	
	public Point3D getSize() {
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
	public void render(GLAutoDrawable drawable, double actHeading, double actTilt, double rotorPos, double tailRotorPos) {
        GL2 gl = drawable.getGL().getGL2();
        Point3D myPosition = world.gps(id);
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
        Object3D chopperObject = new Object3D(myPosition, mySize);
        chopperObject.setColor(1.0,  0.0, 0.0, 1.0);
        // Translate the center of chopper to the origin, so rotation doesn't move chopper
        gl.glPushMatrix();
        gl.glTranslated(centerPos.m_x, centerPos.m_y, centerPos.m_z);
        Point3D transformation = world.transformations(id);
        // rotate chopper by heading
        gl.glRotated(transformation.m_x, 0.0, 0.0, -1.0);
        // rotate chopper by tilt
        gl.glRotated(transformation.m_y, -1.0, 0.0, 0.0);
        gl.glTranslated(-centerPos.m_x,  -centerPos.m_y, -centerPos.m_z);
		double objColor[] = chopperObject.getColor();
		float[] bufferArray = World.makeVertexArray(myPosition, mySize);
		if (bufferArray != null)
		{
			gl.glColor4dv(objColor, 0);
			World.drawRectangles(gl,bufferArray, true);
		}
		// Move center position to center of top rotor
		centerPos.m_z += 1.55;
		gl.glTranslated(centerPos.m_x, centerPos.m_y, centerPos.m_z);
		gl.glRotated(rotorPos, 0.0, 0.0, 1.0);
		gl.glTranslated(-centerPos.m_x, -centerPos.m_y, -centerPos.m_z);
		// Draw main rotor
		gl.glBegin(gl.GL_LINES);
		gl.glColor3d(0.7, 0.7, 0.7);
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
}
