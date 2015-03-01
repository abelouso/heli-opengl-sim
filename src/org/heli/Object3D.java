package org.heli;

public class Object3D {
	private Point3D position;
	private Point3D size;
	private double[] color;
	
	public Object3D(Point3D thePos, Point3D theSize) {
		position = thePos;
		size = theSize;
		color = new double[4];
		for (int i = 0; i < 4; ++i)
		{
			color[i] = 1.0;
		}
	}

	public boolean collidesWith(Object3D other)
	{
		boolean doesItCollide = false;
		Point3D otherPos = other.getPosition();
		Point3D otherSize = other.getSize();
		// TODO: Implement basic bounds checking
		return doesItCollide;
	}
	
	public void setColor(double red, double green, double blue, double alpha)
	{
		if (color == null)
		{
			color = new double[4];
		}
		color[0] = red;
		color[1] = green;
		color[2] = blue;
		color[3] = alpha;
	}
	
	public void setColor(Point3D rgb, double alpha)
	{
	    if(color == null)
	    {
	        color = new double[4];
	    }
	    color[3] = alpha;
	    color[0] = rgb.m_x;
	    color[1] = rgb.m_y;
	    color[2] = rgb.m_z;
	}
	
	public double[] getColor() {
		return color;
	}
	
	public Point3D getPosition() {
		return position;
	}
	
	public Point3D getSize() {
		return size;
	}
}
