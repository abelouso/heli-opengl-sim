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
	
	private static final double FULL_BLOCK_SIZE = 100.0;

	private static final double STREET_OFFSET = 3.0;
	
	private static final double SIDEWALK_OFFSET = 2.0;
	
	private static final double BLOCK_SIZE = FULL_BLOCK_SIZE - 2.0 * STREET_OFFSET;
	
	private static final double SQUARE_SIZE = BLOCK_SIZE - 2.0 * SIDEWALK_OFFSET;
	
	private static final double BUILDING_SPACE = (SQUARE_SIZE / 10.0);
	
	private static final double BUILDING_SIZE = 0.9 * BUILDING_SPACE;
	
	private static final double HOUSES_PER_BLOCK = 10.0;
	
	private Camera camera;
	
	private double maxTime = 10000.0;
	
	private ArrayList<Object3D> worldState;
	
	private Map<Integer, ChopperAggregator> myChoppers;
	
	/**
	 * @param args
	 * @throws Exception 
	 */
	public World(String[] args) throws Exception
	{
		sizeX = 1000;
		sizeY = 1000;
		sizeZ = 200;
		myChoppers = new HashMap<Integer, ChopperAggregator>();
		int chopperID = requestNextChopperID();
		StigChopper myChopper = new StigChopper(chopperID, this);
		Point3D startPos = getStartingPosition(chopperID);
		ChopperInfo chopInfo = new ChopperInfo(this, chopperID, startPos, 0.0);
		ChopperAggregator myAggregator = new ChopperAggregator(myChopper, chopInfo);
		myChoppers.put(chopperID, myAggregator);
		requestSettings(chopperID, ChopperInfo.MAX_MAIN_ROTOR_SPEED, 0.0, ChopperInfo.STABLE_TAIL_ROTOR_SPEED);
		worldState = new ArrayList<Object3D>();
		
		// Generate the world... TODO: Move to city blocks
		for (int row = 0; row < 10; ++row)
		{
			for (int col = 0; col < 10; ++col)
			{
				// Generate a city block
				// TODO: Move to CityBlock class
				// For now, streets are 6.0 m wide
				// and Sidewalks are 3.0 m wide
				double startX = FULL_BLOCK_SIZE * col + STREET_OFFSET;
				double endX = startX + BLOCK_SIZE;
				double startY = FULL_BLOCK_SIZE * row + STREET_OFFSET;
				double endY = startY + BLOCK_SIZE;
				// Sidewalks are 0.1 m above street
				Point3D sidewalkPos = new Point3D(startX, startY, 0.0);
				Point3D sidewalkSize = new Point3D(BLOCK_SIZE, BLOCK_SIZE, 0.1);
				Object3D sidewalk = new Object3D(sidewalkPos, sidewalkSize);
				double startZ = 0.1;
				sidewalk.setColor(0.8, 0.8, 0.8, 1.0);
				worldState.add(sidewalk);
				startX += 0.05 * BUILDING_SPACE + SIDEWALK_OFFSET;
				startY += 0.05 * BUILDING_SPACE + SIDEWALK_OFFSET;
				for (int houseIndex = 0; houseIndex < Math.round(HOUSES_PER_BLOCK); ++houseIndex)
				{
					Object3D leftHouse = makeHouse(startX, startY + houseIndex * BUILDING_SPACE, startZ);
					worldState.add(leftHouse);
					Object3D rightHouse = makeHouse(startX + 9 * BUILDING_SPACE, startY + houseIndex * BUILDING_SPACE, startZ);
					worldState.add(rightHouse);
					if (houseIndex == 0 || houseIndex == 9)
					{
						continue;
					}
					Object3D topHouse = makeHouse(startX + houseIndex * BUILDING_SPACE, startY, startZ);
					worldState.add(topHouse);
					Object3D bottomHouse = makeHouse(startX  + houseIndex * BUILDING_SPACE, startY + 9 * BUILDING_SPACE, startZ);
					worldState.add(bottomHouse);
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

	// TODO: Provide for random starting positions, but for now, start them
	// on main street
	public Point3D getStartingPosition(int chopperID)
	{
		Point3D startPos = new Point3D(480.0 + 10.0 * chopperID, 500.0, 0.0);
		return startPos;
	}
	
	/** Return the chopper with the specified ID
	 * or null if that chopper doesn't exist
	 * @param chopperID ID of the desired chopper
	 * @return
	 */
	public StigChopper getChopper(int chopperID) {
		ChopperAggregator resAggregator = null;
		StigChopper resChopper = null;
		if (myChoppers.containsKey(chopperID))
		{
			resAggregator = myChoppers.get(chopperID);
			resChopper = resAggregator.getChopper();
		}
		return resChopper;
	}
	
	/** Return the chopper info with the specified ID
	 * or null if that chopper doesn't exist
	 * @param chopperID ID of the desired chopper
	 * @return
	 */
	public ChopperInfo getChopInfo(int chopperID)
	{
		ChopperAggregator resAggregator = null;
		ChopperInfo resInfo = null;
		if (myChoppers.containsKey(chopperID))
		{
			resAggregator = myChoppers.get(chopperID);
			resInfo = resAggregator.getInfo();
		}
		return resInfo;
	}
	
	public void requestSettings(double chopperID, double mainRotorSpeed, double tiltAngle, double tailRotorSpeed)
	{
		ChopperAggregator resAggregator = null;
		ChopperInfo resInfo = null;
		if (myChoppers.containsKey(chopperID))
		{
			resAggregator = myChoppers.get(chopperID);
			resInfo = resAggregator.getInfo();
			if (resInfo != null)
			{
				resInfo.requestMainRotorSpeed(mainRotorSpeed);
				resInfo.requestTailRotorSpeed(tailRotorSpeed);
				resInfo.requestTiltLevel(tiltAngle);
			}
		}
		
	}
	public void updateCamera(GL2 gl, int width, int height) {
	    camera.tellGL(gl, width, height);
	    System.out.println("Updated camera with vp size (" + width + ", " + height + ")");
	}
	
	public int requestNextChopperID() { return nextChopperID++; }
	
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
			Iterator it = myChoppers.entrySet().iterator();
			while (it.hasNext())
			{
				Map.Entry pairs = (Map.Entry)it.next();
				int id = (int) pairs.getKey();
				ChopperAggregator locData = (ChopperAggregator) pairs.getValue();
				if (locData != null)
				{
					ChopperInfo chopInfo = locData.getInfo();
					if (chopInfo != null)
					{
						chopInfo.fly(TICK_TIME);
					}
				}
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
	
	public Point3D gps(int chopperID)
	{
		ChopperAggregator thisAg = null;
		Point3D actPosition = null;
		if (myChoppers.containsKey(chopperID))
		{
			thisAg = myChoppers.get(chopperID);
			ChopperInfo thisInfo = thisAg.getInfo();
			actPosition = thisInfo.getPosition();
		}
		return actPosition;
	}
	
	/** This method returns heading, pitch, and zero in a single vector
	 *  Since they're needed in radians for rotations, we'll convert it here
	 * @param chopperID
	 * @return
	 */
	public Point3D transformations(int chopperID)
	{
		Point3D resultVector = new Point3D();
		ChopperAggregator thisAg = null;
		Point3D actPosition = null;
		if (myChoppers.containsKey(chopperID))
		{
			thisAg = myChoppers.get(chopperID);
			ChopperInfo thisInfo = thisAg.getInfo();
			double heading_radians = thisInfo.getHeading() * Math.PI / 180.0;
			resultVector.m_x = heading_radians;
			double pitch_radians = thisInfo.getTilt() * Math.PI / 180.0;
			resultVector.m_y = pitch_radians;
		}
		return resultVector;
	}
	
	public void render(GLAutoDrawable drawable)
	{
		// different transformations
        GL2 gl = drawable.getGL().getGL2();
    	camera.tellGL(gl);
        camera.approach(0.75);
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
			Point3D helipadCenter = new Point3D(objectLoc.m_x + (objectSize.m_x / 2.0), objectLoc.m_y + (objectSize.m_y / 2.0), objectLoc.m_z + objectSize.m_z);
			drawHelipad(gl, helipadCenter.m_x, helipadCenter.m_y, helipadCenter.m_z, objectSize.m_x + 0.05);
		}
		gl.glBegin(gl.GL_QUADS);
		gl.glColor3d(1.0, 0.8, 0.8);
		gl.glVertex3d(497.0, 503.0,  0.0);
		gl.glVertex3d(497.0, 497.0, 0.0);
		gl.glVertex3d(503.0, 497.0, 0.0);
		gl.glVertex3d(503.0, 503.0, 0.0);
		gl.glEnd();
		drawHelipad(gl, 500.0, 500.0, 0.05, 6.0);
	}
	
	public void drawHelipad(GL2 gl, double xCenter, double yCenter, double zHeight, double size)
	{
		double sizeIncrement = size / 6.0;
		gl.glBegin(gl.GL_QUADS);
		gl.glColor3d(0.0, 0.0, 1.0);
		// Left Side H
		gl.glVertex3d(xCenter - 2.0 * sizeIncrement, yCenter + 2.0 * sizeIncrement, zHeight);
		gl.glVertex3d(xCenter - 2.0 * sizeIncrement, yCenter - 2.0 * sizeIncrement, zHeight);
		gl.glVertex3d(xCenter - 1.0 * sizeIncrement, yCenter - 2.0 * sizeIncrement, zHeight);
		gl.glVertex3d(xCenter - 1.0 * sizeIncrement, yCenter + 2.0 * sizeIncrement, zHeight);
		// Right Side H
		gl.glVertex3d(xCenter + 1.0 * sizeIncrement, yCenter + 2.0 * sizeIncrement, zHeight);
		gl.glVertex3d(xCenter + 1.0 * sizeIncrement, yCenter - 2.0 * sizeIncrement, zHeight);
		gl.glVertex3d(xCenter + 2.0 * sizeIncrement, yCenter - 2.0 * sizeIncrement, zHeight);
		gl.glVertex3d(xCenter + 2.0 * sizeIncrement, yCenter + 2.0 * sizeIncrement, zHeight);
		// Middle H
		gl.glVertex3d(xCenter - 1.0 * sizeIncrement, yCenter + 0.5 * sizeIncrement, zHeight);
		gl.glVertex3d(xCenter - 1.0 * sizeIncrement, yCenter - 0.5 * sizeIncrement, zHeight);
		gl.glVertex3d(xCenter + 1.0 * sizeIncrement, yCenter - 0.5 * sizeIncrement, zHeight);
		gl.glVertex3d(xCenter + 1.0 * sizeIncrement, yCenter + 0.5 * sizeIncrement, zHeight);
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
