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
    public static final double CHANGE_INC = 10.0;
    public static final double HOLD_INC = 0.1;
    public static final double INIT_SPEED = 10.0;
    protected World m_world;
    protected double m_target = 0.0;
    protected Apachi m_chopper;
    protected double m_tol = 2.0; //meters
    protected double m_inc = CHANGE_INC; //speed increment in rpm
    
    protected double m_lastAlt = -1.0;
    protected double m_lastVel = -1.0;
    protected double m_lastDelta = m_target;
    protected boolean m_up = true;
    
    protected int m_tick_ms = 200;
    protected double tS = 0.001 * m_tick_ms;
    
    public ApachiAlt(Apachi chop, World world)
    {
        m_world = world;
        m_chopper = chop;
        World.dbg(TAG,"Staring altitude loop",DBG);
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
                double alt = pos.m_z;
                double delta = Math.abs(m_target - alt);
                double diff = Math.abs(delta - m_lastDelta);
                boolean pastLevel = m_up?(alt > m_target):(m_target > alt);
                boolean atAlt = delta <= m_tol;
                double vVel = (alt - m_lastAlt) / (tS);
                double cAcc = (vVel - m_lastVel) / tS;
                double tm = 0.08 * tS;
                double estAlt = alt + tm * vVel + 0.5 * cAcc * tm * tm;
                World.dbg(TAG,"vel: " + Apachi.f(vVel) + " acc: " + Apachi.f(cAcc) + ", est alt: " + Apachi.f(estAlt),DBG);
                World.dbg(TAG,"alt: " + Apachi.f(alt)
                        + ", lastAlt: " + Apachi.f(m_lastAlt)
                        + ", target: " + Apachi.f(m_target)
                        + ", diff: " + Apachi.f(diff)
                        + ", delta: " + Apachi.f(delta)
                        + ", lastD: " + Apachi.f(m_lastDelta)
                        + ", pastLevel: " + pastLevel
                        + ", atAlt: " + atAlt,DBG);

                double newSpeed = m_chopper.estHoverSpeed();
                if(diff < 0.001 && Math.abs(alt) < 0.001)
                {
                    //adjust speed until differences is felt
                    //adjustRotorSpeed(alt, CHANGE_INC);
                    m_chopper.setDesiredRotorSpeed(newSpeed);
                }
                else 
                {                        
                    World.dbg(TAG, "Setting RPM: " + Apachi.f(newSpeed), DBG);

                    m_chopper.setDesiredRotorSpeed(newSpeed);
                    /*
                    if(Math.abs(estAlt - m_target) < (2.0 * m_tol))
                    {
                        World.dbg(TAG, "Setting RPM: " + Apachi.f(newSpeed), DBG);
                        m_chopper.setDesiredRotorSpeed(newSpeed);
                    }
                    if(!atAlt)
                    {
                        adjustRotorSpeed(alt, HOLD_INC);
                    }
                    else
                    {
                        m_chopper.setDesiredRotorSpeed(newSpeed);
                    }
                */
                }
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
        m_target = alt;
    }
    
    void adjustRotorSpeed(double alt, double inc)
    {
        double newSpeed = m_chopper.getCurrentRotorSpeed();
        if(newSpeed > 0.0)
        {
            World.dbg(TAG,"Current rotor speed " + Apachi.f(newSpeed) + ", ",DBG);
            if(alt > m_target)
            {
                //this is dangerous, if rotor speed is too slow
                //crash can occur
                //check the last alt if falling, don't do it
                if(m_lastAlt >= 0.0 && m_lastAlt < alt)
                {
                    newSpeed -= inc;
                }
                else
                {
                }
            }
            else
            {
                if(m_lastAlt >= 0.0 && m_lastAlt >= alt)
                {
                    newSpeed += inc;
                }
                else
                {
                }
            }
        }
        else
        {
            newSpeed = INIT_SPEED;
        }
        World.dbg(TAG,"desired " + Apachi.f(newSpeed),DBG);
        m_chopper.setDesiredRotorSpeed(newSpeed);
    }
    public void changeSpeed(boolean faster, double inc)
    {
        double delta = faster?(inc):(-1.0 * inc);
        World.dbg(TAG,"Adjust speed by " + Apachi.f(delta),DBG);
        m_chopper.setDesiredRotorSpeed(m_chopper.getCurrentRotorSpeed() + delta);
                
    }
}
