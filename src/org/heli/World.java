package org.heli;
import java.util.*;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.lang.*;
import java.math.*;

import javax.media.opengl.GL;
import javax.media.opengl.GL2;
import javax.media.opengl.GLAutoDrawable;
import javax.media.opengl.glu.GLU;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;

/** World Class, for StigChoppers.  Defines the world.
 * Copyright 2015, Daniel A. LaFuze
 * @author dlafuze
 *
 */
public class World
{
	private int nextChopperID = 0;
	private int sizeX;
	private int sizeY;
	private int sizeZ;
	private GLU glu;
	private double[] chop1Color;
	private double[] chop2Color;
	double curTimeStamp = 0.0;
	private static final double TICK_TIME = 1.0 / 30.0;
	
	private static final double THRUST_PER_RPM = 11.1111; // N (kg * m/s^2)
	
	private static final double EARTH_ACCELERATION = -9.80665; // m/s^2
	
	private static final double FUEL_PER_REVOLUTION = 1.0 / 60.0; // Liters
	
	private static final double BLOCK_SIZE = 100.0;

	private static final double SIDEWALK_OFFSET = 3.0;
	
	private static final double SQUARE_SIZE = BLOCK_SIZE - 2.0 * SIDEWALK_OFFSET;
	
	private static final double BUILDING_SPACE = (SQUARE_SIZE / 10.0);
	
	private static final double BUILDING_SIZE = 0.9 * BUILDING_SPACE;
	
	private static final double HOUSES_PER_BLOCK = 10.0;
	
	private Camera camera;
	
	private double maxTime = 10000.0;
	
	private ArrayList<Object3D> worldState;
	
	private ArrayList<StigChopper> myChoppers;
	
	/**
	 * @param args
	 * @throws Exception 
	 */
	public World(String[] args) throws Exception
	{
		sizeX = 1000;
		sizeY = 1000;
		sizeZ = 200;
		myChoppers = new ArrayList<StigChopper>();
		StigChopper myChopper = new StigChopper(requestNextChopperID(), this);
		worldState = new ArrayList<Object3D>();
		myChoppers.add(myChopper);
		
		// Generate the world... TODO: Move to city blocks
		for (int row = 0; row < 10; ++row)
		{
			for (int col = 0; col < 10; ++col)
			{
				// Generate a city block
				// TODO: Move to CityBlock class
				// For now, streets are 6.0 m wide
				// and Sidewalks are 3.0 m wide
				double startX = BLOCK_SIZE * col + SIDEWALK_OFFSET;
				double endX = startX + SQUARE_SIZE;
				double startY = BLOCK_SIZE * row + SIDEWALK_OFFSET;
				double endY = startY + SQUARE_SIZE;
				// Sidewalks are 0.1 m above street
				Point3D sidewalkPos = new Point3D(startX, startY, 0.0);
				Point3D sidewalkSize = new Point3D(SQUARE_SIZE, SQUARE_SIZE, 0.1);
				Object3D sidewalk = new Object3D(sidewalkPos, sidewalkSize);
				double startZ = 0.1;
				sidewalk.setColor(0.8, 0.8, 0.8, 1.0);
				worldState.add(sidewalk);
				startX += 0.05 * BUILDING_SPACE;
				startY += 0.05 * BUILDING_SPACE;
				for (int houseIndex = 0; houseIndex < Math.round(HOUSES_PER_BLOCK); ++houseIndex)
				{
					if (houseIndex == 0 || houseIndex == 9) // Only one building on ends
					{
						Object3D cornerHouse = makeCornerHouse(startX, startY, startZ, houseIndex);
						worldState.add(cornerHouse);
					}
					else
					{
						Object3D leftHouse = makeHouse(startX, startY + houseIndex * BUILDING_SPACE, startZ);
						worldState.add(leftHouse);
						Object3D rightHouse = makeHouse(startX + 9 * BUILDING_SPACE, startY + houseIndex * BUILDING_SPACE, startZ);
						worldState.add(rightHouse);
						Object3D topHouse = makeHouse(startX + houseIndex * BUILDING_SPACE, startY, startZ);
						worldState.add(topHouse);
						Object3D bottomHouse = makeHouse(startX  + houseIndex * BUILDING_SPACE, startY + 9 * BUILDING_SPACE, startZ);
						worldState.add(bottomHouse);
					}
				}
			}
		}
		Point3D locPos = new Point3D(30.0, 30.0, 0.0);
		Point3D locSize = new Point3D(40.0, 40.0, Math.random() * 20.0 + 5.0);
		double r = Math.random() * 0.5;
		double g = Math.random() * 0.5 + 0.25;
		double b = Math.random() * 0.5 + 0.5;
		double a = Math.random() * 0.25 + 0.75;
		Object3D newObject = new Object3D(locPos, locSize);
		newObject.setColor(r, g, b, a);
		worldState.add(newObject);
		
		for (String thisArg: args)
		{
			// I want my arguments to be lower case
			String lowerArg = thisArg.toLowerCase();
			// Strip dashes in case they do it the standard way, I don't want to worry about this yet
			// TODO: Worry about this later
			String strippedArg = lowerArg.replace("-", "");
			String[] splits = lowerArg.split(":");
			if (splits.length != 2)
			{
				if (!lowerArg.equals("h"))
				{
					System.out.println("Ignoring improperly formatted argument!");
					continue;
				}
			}
			// TODO: Add sanity checking on all arguments etc.
			switch(splits[0].charAt(0))
			{
			case 'x':
				sizeX = Integer.parseInt(splits[1]);
				break;
			case 'y':
				sizeY = Integer.parseInt(splits[1]);
				break;
			case 'z':
				sizeZ = Integer.parseInt(splits[1]);
				break;
			case 'h':
				System.out.println("Command Line Arguments:");
				System.out.println("-----------------------");
				System.out.println("x:Number (X World Size   -- default 1000)");
				System.out.println("y:Number (Y World Size   -- default 1000)");
				System.out.println("z:Number (z World Size   -- default 1000)");
				System.out.println("h        (This Help Message");
				break;
			default:
				System.out.println("Unhandled command line argument '" + thisArg + "'");
				break;
			}
		}
		glu = new GLU();
		camera = new Camera(sizeX/2, sizeY/2,0, glu);
		System.out.println("World Size (" + sizeX + ", " + sizeY + ", " + sizeZ + ")");
		System.out.println("Creating world...");
	}

	public void updateCamera(GL2 gl, int width, int height) {
	    camera.tellGL(gl, width, height);
	    System.out.println("Updated camera with vp size (" + width + ", " + height + ")");
	}
	
	public int requestNextChopperID() { return nextChopperID++; }
	
	public Object3D makeCornerHouse(double startX, double startY, double startZ, double houseIndex)
	{
		Object3D worldObj = makeHouse(startX + houseIndex * BUILDING_SPACE, startY + houseIndex * BUILDING_SPACE, startZ);
		return worldObj;
	}
	
	public Object3D makeHouse(double posX, double posY, double posZ)
	{
		double buildingHeight = computeBuildingHeight();
		Point3D buildingPos = new Point3D(posX, posY, posZ);
		Point3D buildingSize = new Point3D(BUILDING_SIZE, BUILDING_SIZE, buildingHeight);
		Object3D worldObj = new Object3D(buildingPos, buildingSize);
		worldObj.setColor(0.6, 0.6 + 0.4 * Math.random(), 0.6 + 0.4 * Math.random(), 1.0);
		return worldObj;
	}
	
	public double computeBuildingHeight()
	{
		double buildingHeight = 10.0 + Math.random() * 10.0;
		double exceptChance = Math.random();
		if (exceptChance >= 0.98)
		{
			buildingHeight *= 5.0;
		}
		else if (exceptChance >= 0.9)
		{
			buildingHeight *= 2.0;
		}
		return buildingHeight;
	}
	
	public double getTick() { return curTimeStamp; }
	
	/** This method returns true if you're out of time
	 * 
	 * @return
	 * @throws Exception 
	 */
	public boolean tick() throws Exception
	{
		boolean outOfTime = false;
		while (curTimeStamp < maxTime)
		{
			for (StigChopper chopper : myChoppers)
			{
				// TODO: Iterate over choppers
			}
			Thread.sleep(10);
			curTimeStamp += TICK_TIME;
		}
		return outOfTime;
	}

	public static float[] makeVertexArray(Point3D inPoint, Point3D boxSize)
	{
		float[] resultArray = null;
		if (inPoint == null)
		{
			return resultArray;
		}
		// 8 vertexes, 3 coordinates each (Add one for center at end)
		resultArray = new float[27];
		float xStart = (float) inPoint.x();
		float yStart = (float) inPoint.y();
		float zStart = (float) inPoint.z();

		float xSize = (float) boxSize.x();
		float ySize = (float) boxSize.y();
		float zSize = (float) boxSize.z();
// Vertex 1
		resultArray[0] = xStart;
		resultArray[1] = yStart + ySize;
		resultArray[2] = zStart + zSize;
		// Vertex 2
		resultArray[3] = xStart;
		resultArray[4] = yStart;
		resultArray[5] = zStart + zSize;
		// Vertex 3
		resultArray[6] = xStart + xSize;
		resultArray[7] = yStart;
		resultArray[8] = zStart + zSize;
		// Vertex 4
		resultArray[9] = xStart + xSize;
		resultArray[10] = yStart + ySize;
		resultArray[11] = zStart + zSize;
		// Vertex 5
		resultArray[12] = xStart;
		resultArray[13] = yStart + ySize;
		resultArray[14] = zStart;
		// Vertex 6
		resultArray[15] = xStart + xSize;
		resultArray[16] = yStart + ySize;
		resultArray[17] = zStart;
		// Vertex 7
		resultArray[18] = xStart + xSize;
		resultArray[19] = yStart;
		resultArray[20] = zStart;
		// Vertex 8
		resultArray[21] = xStart;
		resultArray[22] = yStart;
		resultArray[23] = zStart;
		// Vertex 9 (Extra -- at center)
		resultArray[24] = xStart + xSize / 2.0f;
		resultArray[25] = yStart + ySize / 2.0f;
		resultArray[26] = zStart + zSize / 2.0f;
		return resultArray;
	}
	
	public void render(GLAutoDrawable drawable)
	{
		// different transformations
        GL2 gl = drawable.getGL().getGL2();
    	camera.tellGL(gl);
        camera.approach(1.0);
        gl.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT);

		for (Object3D object : worldState)
		{
			double objColor[] = object.getColor();
			Point3D objectLoc = object.getPosition();
			Point3D objectSize = object.getSize();
			float[] bufferArray = makeVertexArray(objectLoc, objectSize);
			if (bufferArray == null)
			{
				continue;
			}
			gl.glColor4dv(objColor, 0);
			drawRectangles(gl,bufferArray, true);
		}
		gl.glBegin(gl.GL_QUADS);
		gl.glColor3d(1.0,  0.8,  0.4);
		gl.glVertex3d(0.0, 10.0, 0.0);
		gl.glVertex3d(0.0, 0.0, 0.0);
		gl.glVertex3d(10.0, 0.0, 0.0);
		gl.glVertex3d(10.0, 10.0, 0.0);
		gl.glEnd();
	}
	
	public static void drawRectangles(GL2 gl, float[] bufferArray, boolean doLines)
	{
		gl.glBegin(GL2.GL_QUADS);
		// Top face
		gl.glVertex3fv(bufferArray,0);
		gl.glVertex3fv(bufferArray,3);
		gl.glVertex3fv(bufferArray,6);
		gl.glVertex3fv(bufferArray,9);
		// Bottom face
		gl.glVertex3fv(bufferArray,12);
		gl.glVertex3fv(bufferArray,21);
		gl.glVertex3fv(bufferArray,18);
		gl.glVertex3fv(bufferArray,15);
		// Left face
		gl.glVertex3fv(bufferArray,0);
		gl.glVertex3fv(bufferArray,3);
		gl.glVertex3fv(bufferArray,21);
		gl.glVertex3fv(bufferArray,12);
		// Right face
		gl.glVertex3fv(bufferArray,15);
		gl.glVertex3fv(bufferArray,18);
		gl.glVertex3fv(bufferArray,6);
		gl.glVertex3fv(bufferArray,9);
		// Front face
		gl.glVertex3fv(bufferArray,0);
		gl.glVertex3fv(bufferArray,12);
		gl.glVertex3fv(bufferArray,15);
		gl.glVertex3fv(bufferArray,9);
		// Back face
		gl.glVertex3fv(bufferArray,3);
		gl.glVertex3fv(bufferArray,6);
		gl.glVertex3fv(bufferArray,18);
		gl.glVertex3fv(bufferArray,21);
		gl.glEnd();
		if (doLines)
		{
			gl.glColor3d(0.25, 0.25, 0.25);
			// Top face
			gl.glBegin(GL.GL_LINE_LOOP);
			gl.glVertex3fv(bufferArray,0);
			gl.glVertex3fv(bufferArray,3);
			gl.glVertex3fv(bufferArray,6);
			gl.glVertex3fv(bufferArray,9);
			gl.glEnd();
			// Bottom face
			gl.glBegin(GL.GL_LINE_LOOP);
			gl.glVertex3fv(bufferArray,12);
			gl.glVertex3fv(bufferArray,21);
			gl.glVertex3fv(bufferArray,18);
			gl.glVertex3fv(bufferArray,15);
			gl.glEnd();
			// Left face
			gl.glBegin(GL.GL_LINE_LOOP);
			gl.glVertex3fv(bufferArray,0);
			gl.glVertex3fv(bufferArray,3);
			gl.glVertex3fv(bufferArray,21);
			gl.glVertex3fv(bufferArray,12);
			gl.glEnd();
			// Right face
			gl.glBegin(GL.GL_LINE_LOOP);
			gl.glVertex3fv(bufferArray,15);
			gl.glVertex3fv(bufferArray,18);
			gl.glVertex3fv(bufferArray,6);
			gl.glVertex3fv(bufferArray,9);
			gl.glEnd();
			// Front face
			gl.glBegin(GL.GL_LINE_LOOP);
			gl.glVertex3fv(bufferArray,0);
			gl.glVertex3fv(bufferArray,12);
			gl.glVertex3fv(bufferArray,15);
			gl.glVertex3fv(bufferArray,9);
			gl.glEnd();
			// Back face
			gl.glBegin(GL.GL_LINE_LOOP);
			gl.glVertex3fv(bufferArray,3);
			gl.glVertex3fv(bufferArray,6);
			gl.glVertex3fv(bufferArray,18);
			gl.glVertex3fv(bufferArray,21);
			gl.glEnd();
		}

	}
}
