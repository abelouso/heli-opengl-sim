/** Copyright 2015, Dan and Sasha.
 * 
 */

package org.heli;

import javax.swing.JFrame;

import com.jogamp.opengl.GLCapabilities;
import com.jogamp.opengl.GLProfile;
import com.jogamp.opengl.awt.GLCanvas;
import com.jogamp.opengl.util.FPSAnimator;

/** Main program to launch AntRobot program.
 * Copyright 2014
 * @author dlafuze
 *
 */
public class HeliMain
{
	/**
	 * @param args
	 */
	public static void main(String[] args)
	{
		System.out.println("Creating World!");
        GLProfile glp = GLProfile.getDefault();
        GLCapabilities caps = new GLCapabilities(glp);
        caps.setRedBits(8);
        caps.setGreenBits(8);
        caps.setBlueBits(8);
        caps.setAlphaBits(8);
        GLCanvas canvas = new GLCanvas(caps);
		World myWorld = null;
		try
		{
			myWorld = new World(args);
		}
		catch (Exception e)
		{
			System.out.println("Failed to create the world!");
		}
		MainWindow glWin = new MainWindow(myWorld, "Stig Choppers",1000,1000, canvas);
		glWin.setVisible(true);
        canvas.addGLEventListener(glWin.m_glPanel);
        
        // FPSAnimator can be used with desired frames per second as well
        FPSAnimator animator = new FPSAnimator(canvas,50);
        animator.start();

		try
		{
			System.out.println("Starting Time...");
			myWorld.tick();
		}
		catch (Exception e)
		{
			System.out.println("Rule Broken -- timestamp: " + myWorld.getTimestamp() + ", msg: "+ e.toString());
			System.exit(-1);
		}
		// Execute the World
	}

}
