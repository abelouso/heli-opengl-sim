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
//  File Name: 		ApachiSpeed.java
//
//  Author: 		Sasha Beloussov 
//
//  Module Name: 	
// 
//  Creation: 		Mar 1, 2015 3:20:41 PM
//
//  Document/Part #:    
//
//  Description:    
//
//
//


package org.heli;

import java.util.Date;

public class ApachiSpeed extends Thread
{

    public static final String TAG = "ApachiSpeed";
    public static final long DBG = 0x10;
    //TODO create neural network which learns rotor speed for alt
    protected World m_world;
    protected double m_target;
    protected Apachi m_chopper;
    protected double m_tol = 2.0; //meters/sec
    protected double m_inc = 0.09; //tilt increment in deg
    
    protected Point3D m_lastPos;
    protected long m_lastStamp = 0;
    
    protected int m_tick_ms = 500;
    
    public ApachiSpeed(Apachi chop, World world)
    {
        m_world = world;
        m_chopper = chop;
    }
    
    @Override
    public void run()
    {
        //simple feedback loop
        while(true)
        {
            Point3D pos = null;
            long stamp = 0;
            synchronized (m_world)
            {
                pos = m_world.gps(m_chopper.getId());
                stamp = new Date().getTime();
            }
            try
            {
            if(m_lastPos == null)
            {
                m_lastPos = pos;
                m_lastStamp = stamp;
            }
            else
            {
                double dist = pos.distanceXY(m_lastPos);
                double deltaT = (double)(stamp - m_lastStamp);
                double speed = dist / deltaT;
                m_chopper.setCurrentSpeed(speed);
                if(Math.abs(m_target - speed) > m_tol)
                {
                    //need to adjust
                    adjustTilt(speed);
                }
            }
            }
            catch(Exception e)
            {
                World.dbg(TAG,"unable to get chooper info: " + e.toString(),DBG);
            }
            try { Thread.sleep(m_tick_ms);} catch(Exception e){}
        }
    }
    
    synchronized void setTarget(double alt)
    {
        m_target = alt;
    }
    
    void adjustTilt(double speed)
    {
        double newSpeed = m_chopper.getCurrentTilt();
        if(speed > m_target)
        {
            newSpeed -= m_inc;
        }
        else
        {
            newSpeed += m_inc;
        }
        m_chopper.setDesiredTilt(newSpeed);
    }
}
