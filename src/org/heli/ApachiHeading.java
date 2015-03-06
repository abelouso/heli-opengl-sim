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
//  File Name: 		ApachiHeading.java
//
//  Author: 		Sasha Beloussov 
//
//  Module Name: 	
// 
//  Creation: 		Mar 1, 2015 3:13:47 PM
//
//  Document/Part #:    
//
//  Description:    
//
//
//


package org.heli;

public class ApachiHeading extends Thread
{
    public static final String TAG = "ApachiHeading";
    public static final long DBG = 0x10;
    public static final int RT_SLEEP = 90;
    public static final double CHANGE_INC = 8.0; //(rpm)
    //TODO create neural network which learns rotor speed for alt
    protected World m_world;
    protected double m_target = 0.0;
    protected Apachi m_chopper;
    protected double m_tol = 0.02; //degrees
    
    protected Point3D m_lastGPS = null;
    protected double m_lastHeading = -1000.0;
    protected double m_rtToRndRatio = 1.0;
    protected double m_angDist = 0.0;
    protected double m_airSpeed = 0.0;
    protected double m_lastTS = 0.0;
    
    protected int m_tick = RT_SLEEP;
    
    public ApachiHeading(Apachi chop, World world)
    {
        m_world = world;
        m_chopper = chop;
        m_rtToRndRatio = world.timeRatio();
        m_tick = (int)(RT_SLEEP / m_rtToRndRatio);
    }
    
    @Override
    public void run()
    {
        //simple feedback loop
        boolean firstAfterTakeOff = true;
        while(true)
        {
            Point3D dir = null;
            Point3D pos = null;
            synchronized (m_world)
            {
                dir = m_world.transformations(m_chopper.getId());
                pos = m_world.gps(m_chopper.getId());
            }
            try
            {
                double heading = dir.m_x;//dir.headingXY();
                m_chopper.setCurrentHeading(heading);
                long now = (long)(m_world.getTimestamp() * 1000.0);
                double deltaT = (double)(now - m_lastTS);
                double tS = deltaT * 0.001;
                if(m_lastGPS != null)
                {
                    m_airSpeed = 1000.0 * pos.distanceXY(m_lastGPS) / tS; //m/s
                }
                World.dbg(TAG,
                        "current heading (deg): " + Apachi.f(heading)
                        + ", target: " + Apachi.f(m_target)
                        + ", air speed: " + Apachi.f(m_airSpeed)
                        ,DBG);
                if(pos.m_z > 0.0)
                {
                    if(firstAfterTakeOff)
                    {
                        firstAfterTakeOff = false;
                    }
                    //only in flight
                    if(Math.abs(m_target - dir.m_x) > m_tol)
                    {
                        //need to adjust, but only if air speed is slow
                        if(m_airSpeed < 0.03)
                        {
                            adjustStabilizerSpeed(dir.m_x);
                        }
                        else
                        {
                            //make sure we are stable
                            m_chopper.setDesiredStabilizerSpeed(ChopperInfo.STABLE_TAIL_ROTOR_SPEED);
                        }
                    }
                    else
                    {
                        m_chopper.setDesiredStabilizerSpeed(ChopperInfo.STABLE_TAIL_ROTOR_SPEED);
                    }
                }
                else
                {
                    firstAfterTakeOff = true;
                }
                m_lastGPS = pos.copy();
                m_lastHeading = heading;
            }
            catch(Exception e)
            {
                World.dbg(TAG,"unable to get info: " + e.toString(),DBG);
            }

            try { Thread.sleep(m_tick); } catch(Exception e) {};
        }
    }
    
    synchronized void setTarget(double head)
    {
        m_angDist = Math.abs(head - m_target);
        if(m_angDist > 0.0001)
        {
          m_target = head;
        }
    }
    
    void adjustStabilizerSpeed(double head)
    {
        double softHeading = head + 360.0;
        double deltaAngle = Math.abs(head - m_target);
        if(deltaAngle > Math.abs(softHeading - m_target))
        {
            head = softHeading;
            deltaAngle = Math.abs(head - m_target);
        }
        double inc = 0.1 * deltaAngle;
        World.dbg(TAG,
                "################# inc: " + Apachi.f(inc)
                ,0);
        double newSpeed = ChopperInfo.STABLE_TAIL_ROTOR_SPEED;
        if(inc > CHANGE_INC) inc = CHANGE_INC;
        if(head < m_target)
        {
            newSpeed += inc;
        }
        else
        {
            newSpeed -= inc;
        }
        World.dbg(TAG,"adjusting Tail " + newSpeed,DBG);
        m_chopper.setDesiredStabilizerSpeed(newSpeed);
    }
}
