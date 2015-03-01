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

    //TODO create neural network which learns rotor speed for alt
    protected World m_world;
    protected double m_target;
    protected Apachi m_chopper;
    protected double m_tol = 0.02; //degrees
    protected double m_inc = 1.0; //speed increment in rpm
    
    protected int m_tick_ms = 500;
    
    public ApachiHeading(Apachi chop, World world)
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
            synchronized (m_world)
            {
                pos = m_world.transformations(m_chopper.getId());
            }
            if(Math.abs(m_target - pos.m_x) > m_tol)
            {
                //need to adjust
                adjustStabilizerSpeed(pos.m_x);
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
    
    void adjustStabilizerSpeed(double head)
    {
        double newSpeed = m_chopper.getStabilizerSpeed();
        //TODO figure out which way here
        if(head > m_target)
        {
            newSpeed -= m_inc;
        }
        else
        {
            newSpeed += m_inc;
        }
        m_chopper.setDesiredStabilizerSpeed(newSpeed);
    }
}
