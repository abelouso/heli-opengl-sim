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
    public static final double CHANGE_INC = 1.0;
    public static final double HOLD_INC = 1.0;
    public static final double INIT_SPEED = 359.0;
    protected World m_world;
    protected double m_target = 0.0;
    protected Apachi m_chopper;
    protected double m_tol = 2.0; //meters
    protected double m_inc = CHANGE_INC; //speed increment in rpm
    protected double m_lastDelta = 1000.0;
    protected boolean m_up = true;
    protected double m_takeOffSpeed = -1.0;
    
    protected int m_tick_ms = 500;
    
    public ApachiAlt(Apachi chop, World world)
    {
        m_world = world;
        m_chopper = chop;
        System.out.println("Staring altitude loop");
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
                System.out.println("ApachiAlt: alt: " + alt 
                        + ", target: " + m_target
                        + ", diff: " + diff
                        + ", delta: " + delta
                        + ", lastD: " + m_lastDelta
                        + ", pastLevel: " + pastLevel
                        + ", atAlt: " + atAlt);
                if(diff < 0.001)
                {
                    //adjust speed until differences is felt
                    adjustRotorSpeed(alt, CHANGE_INC);
                }
                else
                {
                    if(pastLevel && !atAlt)
                    {
                        adjustRotorSpeed(alt,HOLD_INC);
                    }
                }
                m_lastDelta = delta;
            }
            catch(Exception e)
            {
                System.out.println("ApachiAlt: Unable to get position: " + e.toString());
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
        m_target = alt;
    }
    
    void adjustRotorSpeed(double alt, double inc)
    {
        double newSpeed = m_chopper.getCurrentRotorSpeed();
        if(newSpeed > 0.0)
        {
            System.out.print("ApachiAlt: Current rotor speed " + newSpeed + ", ");
            if(alt > m_target)
            {
                newSpeed -= inc;
            }
            else
            {
                newSpeed += inc;
            }
        }
        else
        {
            newSpeed = INIT_SPEED;
        }
        System.out.println("desired " + newSpeed);
        m_chopper.setDesiredRotorSpeed(newSpeed);

    }
}
