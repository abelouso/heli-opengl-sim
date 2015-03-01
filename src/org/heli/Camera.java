package org.heli;


import javax.media.opengl.GL;
import javax.media.opengl.GL2;
import javax.media.opengl.glu.GLU;

/** This class defines a camera in three space.
 * Future Optimizations: Animations, such as chase mode
 * Copyright 2015
 * @author Daniel LaFuze
 *
 */
public class Camera {
	/** This defines where the camera is located.
	 * 
	 */
	Point3D source;
	
	double orbitAltitude;
	
	double orbitRadius;
	
	private GLU glu;
	
	/** This defines where the camera is looking.  By default, it's facing the
	 * origin.
	 */
	Point3D target;
	
	/** This defines which direction is up.  It is intended to be a
	 * unit vector, though OpenGL isn't picky about the magnitude.
	 */
	Point3D upUnit;
	
	/** This specifies the field of view of the camera
	 * By default, it's 60 degrees.
	 */
	double fovDegrees;
	
	/** This specifies the near clipping distance, by default it's 1 unit.
	 * 
	 */
	double nearClip;
	
	int sceneWidth;
	
	int sceneHeight;
	
	/** This specifies the far clipping distance, by default it's 100 units.
	 * 
	 */
	double farClip;
	
	/** This is used for rotating (sines/cosines) -- in radians
	 * 
	 */
	double curAngle;

	public Camera(int trgX, int trgY, int trgZ, GLU theGLU) {
		// TODO: Compute source position such that default field of view
		// shows the whole thing... By default, camera source is up along
		// z axis
		orbitAltitude = 100.0;
		orbitRadius = trgX;
		source = new Point3D((double)(-trgX),(double)trgY,orbitAltitude);
		target = new Point3D((double)trgX, (double)trgY, (double)trgZ);
		upUnit = new Point3D(0.0,0.0,1.0);
		fovDegrees = 60.0;
		nearClip = 5.0;
		farClip = 1500.0;
		glu = theGLU;
		System.out.println("Camera at " + source.info() + " looking at " + target.info());
	}
	
	/** This constructor for a camera sets the defaults
	 * 
	 */
	public Camera(GLU theGLU) {
		source = new Point3D(0.0,0.0,5.0);
		target = new Point3D();
		upUnit = new Point3D(0.0,0.0,1.0);
		fovDegrees = 60.0;
		nearClip = 1.0;
		farClip = 100.0;
		glu = theGLU;
		sceneWidth = 100; // default, override with tellGL on resize
		sceneHeight = 100;
		curAngle = 0.0;
	}
	
	public void setTarget(Point3D inPoint)
	{
		target = inPoint;
	}
	
	/**
	 * This method allows the camera to move randomly
	 * @param radius
	 */
	public void wobble(double radius) {
		double deltaX = 2.0 * Math.random() - 1.0;
		double deltaY = 2.0 * Math.random() - 1.0;
		double deltaZ = 2.0 * Math.random() - 1.0;
		Point3D newPoint = new Point3D(source.x() + deltaX, source.y() + deltaY, source.z() + deltaZ);
		source = newPoint;
	}
	
	public void chase(Point3D newTarget, double minDistance)
	{
		if (minDistance < nearClip)
		{
			minDistance = nearClip;
		}
		target = newTarget;
		double actDistance = eyeDistance();
		if (actDistance > minDistance * 1.1)
		{
			approach(0.5 * (actDistance / minDistance));
		}
	}
	
	public void chase(Point3D newTarget)
	{
		target = newTarget;
		approach(1.0);
	}
	
	double eyeDistance()
	{
		double deltaZ = source.z() - target.z();
		double deltaY = source.y() - target.y();
		double deltaX = source.x() - target.x();
		double magnitude = Math.sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
		return magnitude;
	}
	
	public void approach(double approachPercent) {
		double deltaZ = approachPercent / 100.0 * (source.z() - target.z());
		double deltaY = approachPercent / 100.0 * (source.y() - target.y());
		double deltaX = approachPercent / 100.0 * (source.x() - target.x());
		double magnitude = Math.sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ);
		source.m_x = source.m_x - deltaX;
		source.m_y = source.m_y - deltaY;
		source.m_z = source.m_z - deltaZ;
	}
	
	public void orbit(double ticksPerRevolution) {
		if (ticksPerRevolution < 60.0)
		{
			ticksPerRevolution = 60.0;
		}
		curAngle += Math.PI /ticksPerRevolution;
		double deltaX = orbitRadius * Math.sin(curAngle);
		double deltaY = orbitRadius * Math.cos(curAngle);
		Point3D newSource = new Point3D(target.x() + deltaX, target.y() + deltaY, target.z() + orbitAltitude);
		source = newSource;
	}
	
	public void tellGL(GL2 gl, int w, int h)
	{
		sceneWidth = w;
		sceneHeight = h;
		tellGL(gl);
	}
	
	private void show()
	{
		System.out.println("Camera at: " + source.info());
		System.out.println("Camera Looking at: " + target.info());
	}
	
	public void tellGL(GL2 gl)
	{
		gl.glMatrixMode(gl.GL_PROJECTION);
		gl.glLoadIdentity();
		
		// Perspective
		if (sceneHeight == 0) // paranoid div/0 check
		{
			sceneHeight = 1;
		}
		double aspectRatio = (double) sceneWidth / (double) sceneHeight;
		glu.gluPerspective(fovDegrees, aspectRatio, nearClip,  farClip);
		glu.gluLookAt((float)source.x(), (float)source.y(), (float)source.z(),
				(float)(target.x()), (float)(target.y()), (float)(target.z()),
				(float)(upUnit.x()), (float)(upUnit.y()), (float)(upUnit.z()));
		
		gl.glMatrixMode(gl.GL_MODELVIEW);
		gl.glLoadIdentity();
	}
}
