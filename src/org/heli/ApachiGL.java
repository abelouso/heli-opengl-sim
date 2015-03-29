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
//  File Name: 		ApachiGL.java
//
//  Author: 		Sasha Beloussov 
//
//  Module Name: 	
// 
//  Creation: 		Mar 1, 2015 2:45:09 PM
//
//  Document/Part #:    
//
//  Description:    
//
//
//


package org.heli;

import com.jogamp.opengl.GL;
import com.jogamp.opengl.GL2;


/**
 * helper class for Apachi Open GL transformations
 * @author abelouso
 *
 */
public class ApachiGL
{

    /**
     * ::toFA convert point 3D into float array
     * @param p
     * @return
     */
    public float[] toFA(Point3D p)
    {
        float res[] = new float[] 
                {
                    (float)(p.x()), 
                    (float)(p.y()),
                    (float)(p.z())
                };
        return res;
    }

    /**
     * ::toFA converts pint 3d into float array with for elements
     * @param p
     * @param nx
     * @return
     */
    public float[] toFA(Point3D p, float nx)
    {
        float res[] = new float[] 
                {
                    (float)(p.x()), 
                    (float)(p.y()),
                    (float)(p.z()),
                    nx
                };
        return res;
    }
    /**
     * ::setEmission sets material Emission
     * @param gl
     * @param col
     */
    public void setEmission(GL2 gl, Point3D col)
    {
        gl.glMaterialfv(GL.GL_FRONT_AND_BACK, GL2.GL_EMISSION, toFA(col,0), 0);
    }
    
    /**
     * ::setMaterial sets material
     * @param gl
     * @param color
     * @param spec
     * @param alpha
     * @param shine
     * @param amb
     */
    public void setMaterial(GL2 gl, Point3D color, Point3D spec, float alpha, float shine, float amb)
    {
        float mat_shine[] = new float[] { shine };
        gl.glMaterialfv(GL.GL_FRONT_AND_BACK
                ,GL2.GL_DIFFUSE, toFA(color,alpha), 0);
        gl.glMaterialfv(GL.GL_FRONT_AND_BACK
                ,GL2.GL_AMBIENT, toFA(Point3D.mult(color,amb),alpha), 0);
        
        gl.glMaterialfv(GL.GL_FRONT_AND_BACK, GL2.GL_SHININESS, mat_shine, 0);
        gl.glMaterialfv(GL.GL_FRONT_AND_BACK, GL2.GL_SPECULAR, toFA(spec,alpha), 0);
    }
    
    /**
     * ::box - draws box in open gl
     * @param gl
     * @param alpha: transparency
     * @param wh: where
     * @param scl: n/a
     * @param size: size of the box
     */
    public void box(GL2 gl, float alpha, Point3D wh, Point3D scl, double size)
    {
        Point3D w = wh;//to3D(wh,scl);
        size = size * 0.5;
        gl.glBegin(GL2.GL_POLYGON);/* f1: front */
        gl.glNormal3f(-1.0f,0.0f,0.0f);
        gl.glVertex3d(w.m_x - size,w.m_y - size,w.m_z - size);
        gl.glVertex3d(w.m_x - size,w.m_y - size,w.m_z + size);
        gl.glVertex3d(w.m_x + size,w.m_y - size,w.m_z + size);
        gl.glVertex3d(w.m_x + size,w.m_y - size,w.m_z - size);
        gl.glEnd();
        gl.glBegin(GL2.GL_POLYGON);/* f2: bottom */

        gl.glNormal3f(0.0f,0.0f,-1.0f);
        gl.glVertex3d(w.m_x - size,w.m_y - size,w.m_z - size);
        gl.glVertex3d(w.m_x + size,w.m_y - size,w.m_z - size);
        gl.glVertex3d(w.m_x + size,w.m_y + size,w.m_z - size);
        gl.glVertex3d(w.m_x - size,w.m_y + size,w.m_z - size);
        gl.glEnd();
        gl.glBegin(GL2.GL_POLYGON);/* f3:back */
        gl.glNormal3f(1.0f,0.0f,0.0f);
        gl.glVertex3d(w.m_x + size,w.m_y + size,w.m_z - size);
        gl.glVertex3d(w.m_x + size,w.m_y + size,w.m_z + size);
        gl.glVertex3d(w.m_x - size,w.m_y + size,w.m_z + size);
        gl.glVertex3d(w.m_x - size,w.m_y + size,w.m_z - size);
        gl.glEnd();
        gl.glBegin(GL2.GL_POLYGON);/* f4: top */
        gl.glNormal3f(0.0f,0.0f,1.0f);
        gl.glVertex3d(w.m_x + size,w.m_y + size,w.m_z + size);
        gl.glVertex3d(w.m_x + size,w.m_y - size,w.m_z + size);
        gl.glVertex3d(w.m_x - size,w.m_y - size,w.m_z + size);
        gl.glVertex3d(w.m_x - size,w.m_y + size,w.m_z + size);
        gl.glEnd();
        gl.glBegin(GL2.GL_POLYGON);/* f5: left */
        gl.glNormal3f(0.0f,1.0f,0.0f);
        gl.glTexCoord2d(0, 0);
        gl.glVertex3d(w.m_x - size,w.m_y - size,w.m_z - size);
        gl.glVertex3d(w.m_x - size,w.m_y + size,w.m_z - size);
        gl.glVertex3d(w.m_x - size,w.m_y + size,w.m_z + size);
        gl.glVertex3d(w.m_x - size,w.m_y - size,w.m_z + size);
        gl.glEnd();
        gl.glBegin(GL2.GL_POLYGON);/* f6: right */
        gl.glNormal3f(0.0f,-1.0f,0.0f);
        gl.glTexCoord2d(0, 0);
        gl.glVertex3d(w.m_x + size,w.m_y - size,w.m_z - size);
        gl.glVertex3d(w.m_x + size,w.m_y - size,w.m_z + size);
        gl.glVertex3d(w.m_x + size,w.m_y + size,w.m_z + size);
        gl.glVertex3d(w.m_x + size,w.m_y + size,w.m_z - size);
        gl.glEnd();
    }
    
}
