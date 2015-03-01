//-*-java-*-
// *************************************************************************
// *                           MODULE SOURCE FILE                          *
// *************************************************************************
//
//           CONFIDENTIAL AND PROPRIETARY INFORMATION   (UNPUBLISHED)
//
//  (Copyright) 2015 Sasha Industries Inc.
//  All Rights Reserved.
//
//  This document  contains confidential and  proprietary  information of
//  Sasha Industries Inc.  and contains patent rights or pending,  trade
//  secrets and or  copyright protected or  pending data  and shall not be
//  reproduced or electronically reproduced or transmitted or disclosed in
//  whole or in part or used for any design or manufacture except when the
//  user possess direct written authorization from Sasha Industries Inc.
//  Its  receipt or possession  does not convey any  rights to  reproduce,
//  disclose its contents,  or to manufacture, use or sell anything it may
//  describe.
//
//  File Name: 		Apachi.java
//
//  Author: 		Sasha Beloussov 
//
//  Module Name: 	
// 
//  Creation: 		Mar 1, 2015 1:55:04 PM
//
//  Document/Part #:    
//
//  Description:    
//
//
//


package org.heli;

import javax.media.opengl.GL;
import javax.media.opengl.GL2;
import javax.media.opengl.GLAutoDrawable;

public class Apachi extends StigChopper
{
    private ApachiAlt m_alt;
    private ApachiHeading m_heading;
    private ApachiSpeed m_speed;
    private ApachiGL m_agl = new ApachiGL();
    
    private double m_rotSpeedR = 0.0;
    private double m_tiltR = 0.0;
    private double m_stabSpeedR = 0.0;
    
    private double m_airSpeed = 0.0;
    
    public Apachi(int id, World world)
    {
        super(id,world);
        System.out.println("Apachi: Construuctor");
        m_alt = new ApachiAlt(this,world);
        m_alt.setTarget(20);
        System.out.println("Apachi: Starting alt loop");
        m_alt.start();
        
        m_heading = new ApachiHeading(this, world);
        m_heading.setTarget(360);
        m_heading.start();

        m_speed = new ApachiSpeed(this, world);
        m_speed.setTarget(0.0);
        m_speed.start();
        
        hover(100);
        //world.requestSettings(id, m_rotSpeedR, m_tiltR, m_stabSpeedR);
        inventory = 16;
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
        chopperObject.setColor(new Point3D(0.7,0.0,1.0),0.98);
        // Translate the center of chopper to the origin, so rotation doesn't move chopper
        gl.glPushMatrix();
        gl.glTranslated(centerPos.m_x, centerPos.m_y, centerPos.m_z);
        Point3D transformation = world.transformations(id);
        // rotate chopper by heading
        gl.glRotated(transformation.m_x, 0.0, 0.0, -1.0);
        // rotate chopper by tilt
        gl.glRotated(transformation.m_y, -1.0, 0.0, 0.0);
        gl.glTranslated(-centerPos.m_x,  -centerPos.m_y, -centerPos.m_z);
        m_agl.setMaterial(gl,new Point3D(0.7,0.0,1.0),new Point3D(0.3,0.3,0.3),0.98f,1.0f,1.0f);
        m_agl.box(gl,0.98f,myPosition,new Point3D(0.0,0.0,0.0),X_SIZE);
        gl.glEnd();
        gl.glPopMatrix();
    }
    
    synchronized public double getCurrentRotorSpeed()
    {
        return 0;
    }
    
    synchronized public void setDesiredRotorSpeed(double newSpeed)
    {
        m_rotSpeedR = newSpeed;
        world.requestSettings(id,m_rotSpeedR,m_tiltR,m_stabSpeedR);
    }
    
    synchronized public double getStabilizerSpeed()
    {
        return 0;
    }
    
    synchronized public void setDesiredStabilizerSpeed(double newSpeed)
    {
        m_stabSpeedR = newSpeed;
        world.requestSettings(id,m_rotSpeedR,m_tiltR,m_stabSpeedR);
    }
    
    synchronized public double getCurrentTilt()
    {
        return world.transformations(id).m_y;
    }
    
    synchronized public void setDesiredTilt(double newTilt)
    {
        m_tiltR = newTilt;
        world.requestSettings(id,m_rotSpeedR,m_tiltR,m_stabSpeedR);
    }
    
    synchronized public void setCurrentSpeed(double speed)
    {
        m_airSpeed = speed;
    }
    
    public void hover(double alt)
    {
        m_alt.setTarget(alt);
        m_speed.setTarget(0.0);
    }
}
