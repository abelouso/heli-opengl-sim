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
}
