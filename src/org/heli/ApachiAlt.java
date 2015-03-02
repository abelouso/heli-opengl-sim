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
    protected World m_world;
    protected double m_target;
    protected Apachi m_chopper;
    protected double m_tol = 2.0; //meters
    protected double m_inc = 3.0; //speed increment in rpm
    
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
            System.out.println("alt: " + pos.m_z + ", target: " + m_target);
            if(Math.abs(m_target - pos.m_z) > m_tol)
            {
                //need to adjust
                adjustRotorSpeed(pos.m_z);
            }
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
        m_target = alt;
    }
    
    void adjustRotorSpeed(double alt)
    {
        double newSpeed = m_chopper.getCurrentRotorSpeed();
        System.out.print("Current rotor speed " + newSpeed + ", ");
        if(alt > m_target)
        {
            newSpeed -= m_inc;
        }
        else
        {
            newSpeed += m_inc;
        }
        System.out.println("desired " + newSpeed);
        m_chopper.setDesiredRotorSpeed(newSpeed);
        
    }
}
