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
//  File Name: 		Heli_GL_Panel.java
//
//  Author: 		Sasha Beloussov 
//
//  Module Name: 	
// 
//  Creation: 		Mar 29, 2015 12:50:46 AM
//
//  Document/Part #:    
//
//  Description:    
//
//
//


package org.heli;

import java.awt.Color;
import java.awt.Graphics;
import java.awt.Transparency;
import java.awt.color.ColorSpace;
import java.awt.image.BufferedImage;
import java.awt.image.ColorModel;
import java.awt.image.ComponentColorModel;
import java.awt.image.DataBuffer;
import java.awt.image.DataBufferByte;
import java.awt.image.Raster;
import java.awt.image.WritableRaster;
import java.io.BufferedInputStream;
import java.io.IOException;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.HashMap;
import java.util.Hashtable;

import javax.imageio.ImageIO;
import javax.swing.JFrame;
import javax.swing.JPanel;

import com.jogamp.opengl.GL;
import com.jogamp.opengl.GL2;
import com.jogamp.opengl.GLAutoDrawable;
import com.jogamp.opengl.GLEventListener;
import com.jogamp.opengl.util.texture.Texture;

public class Heli_GL_Panel extends JPanel implements GLEventListener
{
    /**
     * 
     */
    private static final long serialVersionUID = 7791875830367916958L;
    
    private World theWorld = null;
    private int myWidth = 0;
    private int myHeight = 0;
    private MainWindow m_mainWnd = null;

    private ColorModel glAlphaColorModel;
    private ColorModel glColorModel;

    /** The table of textures that have been loaded in this loader */
    private HashMap<String,Texture> table = new HashMap<String,Texture>();

    public Texture texture = null;
    public int textureID = 0;
    
    public Heli_GL_Panel(MainWindow mw, World world, int h, int w)
    {
        super();
        m_mainWnd = mw;
        theWorld = world;
        myHeight = h;
        myWidth = w;
        textureID = 0;

        glAlphaColorModel = new ComponentColorModel(ColorSpace.getInstance(ColorSpace.CS_sRGB), new int[] { 8, 8, 8, 8 }, true, false, Transparency.TRANSLUCENT, DataBuffer.TYPE_BYTE);
        glColorModel = new ComponentColorModel(ColorSpace.getInstance(ColorSpace.CS_sRGB), new int[] { 8, 8, 8, 0 }, false, false, Transparency.OPAQUE, DataBuffer.TYPE_BYTE);

    }

    @Override
    public void display(GLAutoDrawable drawable)
    {
        render(drawable);

    }

    @Override
    public void dispose(GLAutoDrawable arg0)
    {
        // TODO Auto-generated method stub

    }

    @Override
    public void init(GLAutoDrawable drawable)
    {
        GL gl = drawable.getGL();
        GL2 gl2 = gl.getGL2();
        //texture.setTexParameterf(gl, GL2.GL_TEXTURE_MIN_FILTER, GL2.GL_LINEAR);
        //texture.setTexParameterf(gl, GL2.GL_TEXTURE_MAG_FILTER, GL2.GL_LINEAR);

        theWorld.updateCamera(gl2, myWidth, myHeight);
        // Global settings.
        gl.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA);
        gl.glEnable( GL.GL_BLEND );

        gl.glEnable(GL2.GL_FOG);
        gl2.glFogi(GL2.GL_FOG_MODE, GL2.GL_LINEAR);
        gl2.glHint(GL2.GL_FOG_HINT, GL2.GL_NICEST);
        float fogColor[] = {0.0f, 0.0f, 0.0f, 0.05f };
        gl2.glFogfv( GL2.GL_FOG_COLOR, fogColor, 0 );
        gl2.glFogf(GL2.GL_FOG_START, 0.0f); // Fog Start Depth 
        gl2.glFogf(GL2.GL_FOG_END, 200.0f); // Fog End Depth
        //gl2.glHint(GL2.GL_FOG_HINT, GL2.GL_FASTEST);
        /*
        // TODO: Add options for faster or nicer
        gl2.glFogi( GL2.GL_FOG_COORD_SRC, GL2.GL_FOG_COORD );
        //gl2.glFogi( GL2.GL_FOG_COORD_SRC, GL2.GL_FRAGMENT_DEPTH );
         */

        gl.glEnable(GL.GL_DEPTH_TEST);
        gl.glDepthFunc(GL.GL_LEQUAL);
        //gl2.glShadeModel(GL2.GL_SMOOTH);
        gl2.glShadeModel(GL.GL_SMOOTH_LINE_WIDTH_RANGE);
        gl2.glHint(GL2.GL_PERSPECTIVE_CORRECTION_HINT, GL.GL_NICEST);
        gl.glClearColor(0.0f, 0.0f, 0.0f, 0.0f);

        try
        {
            texture = getTexture("helipad_256.png",gl2);
        }
        catch (IOException e)
        {
            texture = null;
            System.out.println("Couldn't load image -- error: " + e.getMessage());
        }

        System.out.println("Initialized the GL Window");
    }

    @Override
    public void reshape(GLAutoDrawable arg0, int x, int y, int h, int w)
    {
        myWidth = w;
        myHeight = h;
    }
    
    public void render(GLAutoDrawable drawable)
    {
        theWorld.render(drawable, texture);
        m_mainWnd.render(drawable);
    }

    public Texture getTexture(String resourceName, GL2 gl,
            int target, 
            int dstPixelFormat, 
            int minFilter, 
            int magFilter) throws IOException
    {
        int srcPixelFormat = 0;
        
        // create the texture ID for this texture 

        int textureID = genTexture(gl);
        
        // bind this texture 

        gl.glBindTexture(target, textureID); 
 
        BufferedImage bufferedImage = loadImage(resourceName); 
        Texture texture = new Texture(target,textureID, 256, 256, bufferedImage.getWidth(), bufferedImage.getHeight(), false); 
        
        if (bufferedImage.getColorModel().hasAlpha())
        {
            srcPixelFormat = GL.GL_RGBA;
        } 
        else
        {
            srcPixelFormat = GL.GL_RGB;
        }

        // convert that image into a byte buffer of texture data 

        ByteBuffer textureBuffer = convertImageData(bufferedImage,texture); 
        if (target == GL.GL_TEXTURE_2D) 
        { 
            gl.glTexParameteri(target, GL.GL_TEXTURE_MIN_FILTER, minFilter); 
            gl.glTexParameteri(target, GL.GL_TEXTURE_MAG_FILTER, magFilter); 
        } 
 
        // produce a texture from the byte buffer

        try
        {
            gl.glTexImage2D(target, 
                    0, 
                    dstPixelFormat, 
                    get2Fold(bufferedImage.getWidth()), 
                    get2Fold(bufferedImage.getHeight()), 
                    0, 
                    srcPixelFormat, 
                    GL.GL_UNSIGNED_BYTE, 
                    textureBuffer.rewind()); 
        }
        catch (IndexOutOfBoundsException e)
        {
            System.out.println("Couldn't build image buffer, exception: " + e.getMessage());
        }
        
        return texture; 
    } 

    /**
     * Get the closest greater power of 2 to the fold number
     * 
     * @param fold The target number
     * @return The power of 2
     */
    private int get2Fold(int fold)
    {
        int ret = 2;
        while (ret < fold)
        {
            ret *= 2;
        }
        return ret;
    } 
    
    /**
     * Convert the buffered image to a texture
     *
     * @param bufferedImage The image to convert to a texture
     * @param texture The texture to store the data into
     * @return A buffer containing the data
     */
    private ByteBuffer convertImageData(BufferedImage bufferedImage,Texture texture)
    { 
        ByteBuffer imageBuffer = null; 
        WritableRaster raster;
        BufferedImage texImage;
        
        int texWidth = 2;
        int texHeight = 2;
        
        // find the closest power of 2 for the width and height

        // of the produced texture

        while (texWidth < bufferedImage.getWidth())
        {
            texWidth *= 2;
        }
        while (texHeight < bufferedImage.getHeight())
        {
            texHeight *= 2;
        }
        
        // I did these at construction, but it's kind of hard coded
        //texture.setTextureHeight(texHeight);
        //texture.setTextureWidth(texWidth);
        
        // create a raster that can be used by OpenGL as a source

        // for a texture

        if (bufferedImage.getColorModel().hasAlpha())
        {
            raster = Raster.createInterleavedRaster(DataBuffer.TYPE_BYTE,texWidth,texHeight,4,null);
            texImage = new BufferedImage(glAlphaColorModel,raster,false,new Hashtable());
        }
        else
        {
            raster = Raster.createInterleavedRaster(DataBuffer.TYPE_BYTE,texWidth,texHeight,3,null);
            texImage = new BufferedImage(glColorModel,raster,false,new Hashtable());
        }
            
        // copy the source image into the produced image

        Graphics g = texImage.getGraphics();
        g.setColor(new Color(0f,0f,0f,0f));
        g.fillRect(0,0,texWidth,texHeight);
        g.drawImage(bufferedImage,0,0,null);
        
        // build a byte buffer from the temporary image 

        // that be used by OpenGL to produce a texture.

        byte[] data = ((DataBufferByte) texImage.getRaster().getDataBuffer()).getData(); 

        imageBuffer = ByteBuffer.allocateDirect(data.length); 
        imageBuffer.order(ByteOrder.nativeOrder()); 
        imageBuffer.put(data, 0, data.length); 
        
        return imageBuffer; 
    } 
    
    /** 
     * Load a given resource as a buffered image
     * 
     * @param ref The location of the resource to load
     * @return The loaded buffered image
     * @throws IOException Indicates a failure to find a resource
     */
    private BufferedImage loadImage(String ref) throws IOException 
    {
        URL url = MainWindow.class.getClassLoader().getResource(ref);
        if (url == null)
        {
            throw new IOException("Cannot find: "+ref);
        }
        
        BufferedImage bufferedImage = ImageIO.read(new BufferedInputStream(getClass().getClassLoader().getResourceAsStream(ref))); 
 
        return bufferedImage;
    } 

    /**
     * Load a texture
     *
     * @param resourceName The location of the resource to load
     * @return The loaded texture
     * @throws IOException Indicates a failure to access the resource
     */
    public Texture getTexture(String resourceName, GL2 gl) throws IOException {
        Texture tex = (Texture) table.get(resourceName);
        
        if (tex != null) {
            return tex;
        }
        
        tex = getTexture(resourceName, gl,
                         GL.GL_TEXTURE_2D, // target

                         GL.GL_RGBA,     // dst pixel format

                         GL.GL_LINEAR, // min filter (unused)

                         GL.GL_LINEAR);
        
        table.put(resourceName,tex);
        
        return tex;
    }

    private int genTexture(GL gl)
    {
        final int[] tmp = new int[1];
        gl.glGenTextures(1, tmp, 0);
        return tmp[0];
    }
    
}
