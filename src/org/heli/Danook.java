//-*-java-*-
// Copyright 2015, Dan and Sasha
//

package org.heli;

import java.util.ArrayList;

import javax.media.opengl.GL;
import javax.media.opengl.GL2;
import javax.media.opengl.GLAutoDrawable;

public class Danook extends StigChopper
{
    public static final String TAG = "Danook";
    public static final long D_DBG = 0x1;
    
	private DanookController myThread;
	
    public Danook(int id, World world)
    {
        super(id,world);
        myThread = new DanookController(this,world);
        myThread.start();
    }
    
    synchronized public double getCurrentTilt_Degrees()
    {
        return world.transformations(id).m_y;
    }
    
    /** Provide our controller access to our waypoints.
     * 
     * @return the list of waypoints
     */
    synchronized public ArrayList<Point3D> getWaypoints()
    {
    	return targetWaypoints;
    }
    
    @Override
	public void render(GLAutoDrawable drawable, double actHeading, double actTilt, double rotorPos, double tailRotorPos)
	{
		super.render(drawable, actHeading, actTilt, rotorPos, tailRotorPos);
        GL2 gl = drawable.getGL().getGL2();
		Point3D myTarget = myThread.getDestination();
		if (myTarget != null)
		{
			gl.glBegin(gl.GL_TRIANGLE_STRIP);
			gl.glColor4d(1.0, 0.25, 0.25, 0.5);
			gl.glVertex3d(myTarget.m_x - 5.0, myTarget.m_y - 5.0, myTarget.m_z);
			gl.glVertex3d(myTarget.m_x - 5.0, myTarget.m_y + 5.0, myTarget.m_z);
			gl.glVertex3d(myTarget.m_x, myTarget.m_y, myTarget.m_z + 75.0);
			gl.glVertex3d(myTarget.m_x + 5.0, myTarget.m_y + 5.0, myTarget.m_z);
			gl.glVertex3d(myTarget.m_x + 5.0, myTarget.m_y - 5.0, myTarget.m_z);
			gl.glVertex3d(myTarget.m_x - 5.0, myTarget.m_y - 5.0, myTarget.m_z);
			gl.glEnd();
		}

	}
}
