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
//  File Name: 		ApachiAlt.java
//
//  Author: 		Sasha Beloussov 
//
//  Module Name: 	
// 
//  Creation: 		Mar 1, 2015 2:56:36 PM
//
//  Document/Part #:    
//
//  Description:    
//
//
//


package org.heli;

import java.util.Date;

/**
 * this class maintains altitude using a simple feedback loop
 * @author abelouso
 *
 */
public class ApachiAlt extends Thread
{
    //TODO create neural network which learns rotor speed for alt
    public static final String TAG = "ApachiAlt";
    public static final long DBG = 0x10;
    public static final double CHANGE_INC = 20.0;
    public static final double HOLD_INC = 10.0;
    public static final double INIT_SPEED = 10.0;
    public static final int RT_SLEEP = 200;
    protected World m_world;
    protected double m_target = 0.0;
    protected double m_altDist = 0.0;
    protected Apachi m_chopper;
    protected double m_tol = 2.0; //meters
    protected double m_inc = CHANGE_INC; //speed increment in rpm
    
    protected double m_lastAlt = -1.0;
    protected double m_lastVel = -1.0;
    protected double m_lastDelta = m_target;
    protected long m_lastTS = 0;
    protected double m_revs = 0.0;
    protected double m_lastRPM = -1.0;
    protected boolean m_up = true;
    
    protected double m_rtToRndRatio = 1.0;
    protected int m_tick_ms = 200;
    protected double tS = 0.001 * m_tick_ms;
    
    public ApachiAlt(Apachi chop, World world)
    {
        m_world = world;
        m_chopper = chop;
        m_rtToRndRatio = world.timeRatio();
        m_tick_ms = (int)(RT_SLEEP / m_rtToRndRatio);
        tS = 0.001 * m_tick_ms;
        World.dbg(TAG,
                "Staring altitude loop, speed ratio: " + Apachi.f(m_rtToRndRatio)
                + ",tick: " + m_tick_ms
                ,DBG);
    }
    
    @Override
    public void run()
    {
        while(true)
        {
            //simple feedback loop
            Point3D pos = null;
            synchronized (m_world)
            {
                pos = m_world.gps(m_chopper.getId());
            }
            try
            {
                long now = (long)(m_world.getTimestamp() * 1000.0);
                double deltaT = (double)(now - m_lastTS);
                tS = deltaT * 0.001;
                double alt = pos.m_z;
                double delta = Math.abs(m_target - alt);
                double diff = Math.abs(delta - m_lastDelta);
                boolean pastLevel = m_up?(alt > m_target):(m_target > alt);
                boolean atAlt = delta <= m_tol;
                double vVel = (alt - m_lastAlt) / (tS);
                double cAcc = (vVel - m_lastVel) / tS;
                double tm = tS;// / m_rtToRndRatio;
                double estAlt = alt + tm * vVel + 0.5 * cAcc * tm * tm;
                if(m_lastTS > 0 && m_lastRPM > 0.0)
                {
                    m_revs += deltaT * m_lastRPM * 0.001 / 60.0;
                }
                World.dbg(TAG,"vel: " + Apachi.f(vVel) + " acc: " + Apachi.f(cAcc) + ", est alt: " + Apachi.f(estAlt)
                        + ", alt: " + Apachi.f(alt)
                        + ", lastAlt: " + Apachi.f(m_lastAlt)
                        + ", target: " + Apachi.f(m_target)
                        + ", diff: " + Apachi.f(diff)
                        + "\n delta: " + Apachi.f(delta)
                        + ", lastD: " + Apachi.f(m_lastDelta)
                        + ", pastLevel: " + pastLevel
                        + ", atAlt: " + atAlt
                        + ", revs: " + Apachi.f(m_revs)
                        + ", dT: " + Apachi.f(deltaT)
                        + ", rpm: " + Apachi.f(m_lastRPM)
                        ,0);

                double newSpeed = m_chopper.estHoverSpeed(m_revs);
                if(diff < 0.001 && Math.abs(alt) < 0.001)
                {
                    //adjust speed until differences is felt
                    //adjustRotorSpeed(alt, CHANGE_INC);
                    m_lastRPM = m_chopper.setDesiredRotorSpeed(newSpeed + CHANGE_INC);
                }
                else 
                {                        
                    //World.dbg(TAG, "Setting RPM: " + Apachi.f(newSpeed), DBG);
                    //m_lastRPM = m_chopper.setDesiredRotorSpeed(newSpeed);

                    boolean upwards = (m_lastAlt < alt);
                    double startDecel = upwards?(0.1 * m_altDist):(0.13 * m_altDist);
                    World.dbg(TAG,"Start decel: " + Apachi.f(startDecel)
                            + ", distance: " + Apachi.f(m_altDist)
                            + ", est - tar: " + Apachi.f(Math.abs(estAlt - m_target))
                            + ", tol: " + Apachi.f(startDecel * m_tol)
                            ,0);
                    if(Math.abs(estAlt - m_target) < (startDecel * m_tol))
                    {
                        boolean keepDecel = upwards?(vVel > 0.04):(vVel < -0.04);
                        double rat = 2.0;
                        if(Math.abs(vVel) > 2.0) rat = (1.1 * Math.abs(vVel));
                        World.dbg(TAG,
                                "rat lim: " + Apachi.f(2.0)
                                + ", vVel: " + Apachi.f(Math.abs(vVel))
                                + ", rat: " + Apachi.f(rat)
                                + ", change_inc: " + Apachi.f(CHANGE_INC)
                                + ", alt: " + Apachi.f(alt)
                                + ", h spd: " + Apachi.f(newSpeed)
                                ,DBG);
                        if(keepDecel)
                        {
                          newSpeed += (upwards?(-1.0 * rat * CHANGE_INC):1.05 * rat * CHANGE_INC);
                          World.dbg(TAG,"****************** Adjusted speed to " + newSpeed,DBG);
                        }
                        World.dbg(TAG, "Setting RPM: " + Apachi.f(newSpeed), DBG);
                        m_lastRPM = m_chopper.setDesiredRotorSpeed(newSpeed);
                    }
                    //else
                    {
                        if(!atAlt)
                        {
                            World.dbg(TAG,"Not at alt, ajusting",DBG);
                            adjustToTarget(alt, newSpeed, HOLD_INC);
                        }
                        else
                        {
                            World.dbg(TAG,"At alt, howvering ************** ",DBG);
                            m_lastRPM = m_chopper.setDesiredRotorSpeed(newSpeed);
                        }
                    }
                
                }
                m_lastTS = now;
                m_lastVel = vVel;
                m_lastAlt = alt;
                m_lastDelta = delta;
            }
            catch(Exception e)
            {
                World.dbg(TAG,"Unable to get position: " + e.toString(),DBG);
            }
            try
            {
                Thread.sleep(m_tick_ms);
            }
            catch(Exception e)
            {
                //no prob
            }
        }
    }
    
    synchronized void setTarget(double alt)
    {
        m_up = (alt > m_target)?true:false;
        m_lastDelta = Math.abs(alt - m_target);
        if(m_lastDelta > 0.001)
        {
           m_altDist = Math.abs(m_target - alt);
           m_target = alt;
        }
    }
    
    void adjustToTarget(double alt, double howerSpeed, double inc)
    {
        double deltaAlt = Math.abs(alt - m_target);
        inc = 0.9 * deltaAlt;
        if(alt < m_target)
        {
            //going up
            if(inc > CHANGE_INC) inc = CHANGE_INC;
            m_lastRPM = m_chopper.setDesiredRotorSpeed(howerSpeed + inc);
        }
        else
        {
            if(inc > 0.5 * CHANGE_INC) inc = 0.5 * CHANGE_INC;
            m_lastRPM = m_chopper.setDesiredRotorSpeed(howerSpeed - inc);
        }
    }
}
