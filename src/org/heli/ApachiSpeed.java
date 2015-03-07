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
    public static final int RT_SLEEP = 200;
    public static final double CHNGE_INC = 0.2; //deg
    public static final double POS_TILT = 1.0;
    //TODO create neural network which learns rotor speed for alt
    protected World m_world;
    protected double m_target = 0.0;
    protected Apachi m_chopper;
    protected double m_tol = 0.05; //meters/sec
    
    protected Point3D m_lastGPS = null;
    
    protected double m_rtToRndRatio = 1.0;

    protected double m_spdDist = 0.0;
    protected double m_airSpeed = 0.0;
    protected double m_lastTS = 0.0;
    protected double m_targetTime = 0.0;
    protected double m_howLong = 0.0;
    
    protected int m_tick = RT_SLEEP;
    
    public ApachiSpeed(Apachi chop, World world)
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
        while(true)
        {
            Point3D pos = null;
            double heading = 0.0;
            synchronized (m_world)
            {
                heading = m_world.transformations(m_chopper.getId()).m_x;
                pos = m_world.gps(m_chopper.getId());
            }
            try
            {
                double now = pos.m_t;
                double airSpeed = 0.0;
                if(m_howLong > 0.0 && (now - m_targetTime) > m_howLong)
                {
                    World.dbg(TAG,"Stopping, ran for that time",DBG);
                    m_target = 0.0; //stop
                }
                if(m_lastGPS != null)
                {
                    double deltaT = (double)(now - m_lastTS);
                    airSpeed = pos.distanceXY(m_lastGPS) / deltaT; //m/s
                    double dot = pos.headingXY(m_lastGPS);
                    m_chopper.setCurrentSpeed(airSpeed);
                    double dSpeed = Math.abs(airSpeed - m_target);
                    boolean atSpeed = dSpeed < m_tol;
                    double tiltCor = 1.0;//(dSpeed < prevDSpeed)?1.0:-1.0;
                    double accel = (airSpeed - m_airSpeed) / deltaT;
                    //now that we have air speed
                    double startDecel = 0.1 * m_spdDist;
                    double estSpeed = airSpeed + deltaT * accel;
                    World.dbg(TAG,
                            "spd: " + Apachi.f(airSpeed)
                            +",acc: " + Apachi.f(accel)
                            +",estSpeed: " + Apachi.f(estSpeed)
                            + ", DOT: " + Apachi.f(dot)
                            ,DBG);
                        if(Math.abs(estSpeed - m_target) < (startDecel * m_tol))
                        {
                            World.dbg(TAG,"### Decelerating",DBG);
                            boolean keepDecel = Math.abs(accel) > 0.001;
                            if(keepDecel)
                            {
                                m_chopper.setDesiredTilt(POS_TILT * -1.0 * 0.1 * tiltCor * accel);
                            }
                        }
                        if(!atSpeed)
                        {
                            World.dbg(TAG,"@@@@ NOT At speed, adjusting",DBG);
                            adjustTilt(airSpeed, accel, tiltCor);
                        }
                        else
                        {
                            World.dbg(TAG,"@@@@@@@@@@ speed",DBG);
                            m_chopper.setDesiredTilt(0.0);
                        }
                }
                m_airSpeed = airSpeed;
                m_lastGPS = pos.copy();
                m_lastTS = now;
            }
            catch(Exception e)
            {
                World.dbg(TAG,"unable to get chooper info: " + e.toString(),DBG);
            }
            try { Thread.sleep(m_tick);} catch(Exception e){}
        }
    }
    
    synchronized void setTarget(double spd_ms, double time_sec)
    {
        m_spdDist = Math.abs(spd_ms - m_target);
        if(m_spdDist > 0.0001)
        {
            m_target = spd_ms;
            m_howLong = time_sec;
            m_targetTime = m_world.getTimestamp();
        }
    }
    
    void adjustTilt(double speed, double accel, double tiltCor)
    {
        double ds = Math.abs(speed - m_target);
        double inc = 1.0 * ds;
        double tilt = 0.0;
        if(Math.abs(accel) < 15.0)
        {
            if(speed < m_target)
            {
                tilt = tiltCor * POS_TILT * inc;
            }
            else
            {
                tilt = tiltCor * -1.0 * POS_TILT * inc;
            }
        }
        World.dbg(TAG,"seeting tilt: " + Apachi.f(tilt),DBG);
        m_chopper.setDesiredTilt(tilt);
    }
}
