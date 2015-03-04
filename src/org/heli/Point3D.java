package org.heli;

public class Point3D implements Comparable<Point3D>
{
	public static final double EPSILON = 0.2;
	public double m_x = 0;
	public double m_y = 0;
	public double m_z = 0;
	public double m_t = 0;
	
	public Point3D()
	{
		invalidate();
	}
	
	public Point3D(double x, double y, double z)
	{
		m_x = x;
		m_y = y;
		m_z = z;
		m_t = 0.0;
	}
	
	public Point3D(double x, double y, double z, double t)
	{
		m_x = x;
		m_y = y;
		m_z = z;
		m_t = t;
	}
	
	public Point3D copy()
	{
		Point3D res = new Point3D();
		res.m_x = m_x;
		res.m_y = m_y;
		res.m_z = m_z;
		res.m_t = m_t;
		return res;
	}
	
	public int X() { return (int)Math.floor(m_x); };
	
	public int Y() { return (int)Math.floor(m_y); };
	
	public int Z() { return (int)Math.floor(m_z); };
	
	public int T() { return (int)Math.floor(m_t); };
	
	public double x() { return m_x; }
	
	public double y() { return m_y; }
	
	public double z() { return m_z; }
	
	public double t() { return m_t; }
	
	public boolean isValid()
	{
		return m_z >= 0 && m_x >= 0 && m_y >= 0;
	}
	
	public boolean isInWorld(double xm, double ym, double zm)
	{
		return isValid() && x() < (xm - 0) && y() < (ym - 0) && y() < (zm - 0);
	}
	public boolean isInWorld(Point3D loc)
	{
		return isValid() && x() < (loc.x() - 0) && y() < (loc.y() - 0) && z() < (loc.z() - 0);
	}
	
	// TODO: This is no longer a valid method
	public void invalidate()
	{
		m_z = -1.0;
		m_x = -1.0;
		m_y = -1.0;
		m_t = -1.0;
	}
	
	/** This is really a clamp upper
	 * 
	 * @param xm
	 * @param ym
	 * @param zm
	 * @param tm
	 */
	public void validate(double xm, double ym, double zm, double tm)
	{
		m_x = m_x >= xm ? xm : m_x;
		m_y = m_y >= ym ? ym : m_y;
		m_z = m_z >= zm ? zm : m_z;
		m_t = m_t >= tm ? tm : m_t;
	}
	
	public void validate(Point3D pt)
	{
		validate(pt.m_x, pt.m_y, pt.m_z, pt.m_t);
	}
	
	public Point3D left() // west
	{
		Point3D res = copy();
		res.m_x -= 1.0;
		return res;
	}
	
	public Point3D right() // east
	{
		Point3D res = copy();
		res.m_x += 1.0;
		return res;
	}
	
	public Point3D forward() // north
	{
		Point3D res = copy();
		res.m_y += 1.0;
		return res;
	}
	
	public Point3D back() // south
	{
		Point3D res = copy();
		res.m_y -= 1.0;
		return res;
	}
	
	public Point3D up()
	{
		Point3D res = copy();
		res.m_z += 1.0;
		return res;
	}
	
	public Point3D down()
	{
		Point3D res = copy();
		res.m_z -= 1.0;
		return res;
	}
	
	public double distance(Point3D src)
	{
		double x = (m_x - src.m_x);
		double y = (m_y - src.m_y);
		double z = (m_z - src.m_z);
		return Math.sqrt(x * x + y * y + z * z);
	}
	
	public double distanceXY(Point3D src)
	{
		double x = (m_x - src.m_x);
		double y = (m_y - src.m_y);
		return Math.sqrt(x * x + y * y);
	}
	
	@Override
	public 	int hashCode()
	{
		Double d = new Double(distance(new Point3D(0,0,0)));
		return d.hashCode();
	}
	
	//returns atan() of k - angle to x-axis in radians // NOTE: I don't think this is right
	double heading()
	{
		double head = 1.0;
		if(Math.abs(m_x) > 0.01 * EPSILON) head *= Math.atan(m_x / m_y);
		if(Math.abs(m_y) > 0.01 * EPSILON) head *= Math.atan(m_x / m_y);
		if(Math.abs(m_z) > 0.01 * EPSILON) head *= Math.atan(m_y / m_z);
		
		return head;
	}
	
	@Override
	public int compareTo(Point3D pt)
	{
		if(equals(pt)) return 0;
		Point3D pt0 = new Point3D(0,0,0);
		double d1 = pt.distance(pt0) * pt.heading();
		double d0 = distance(pt0) * heading();
		if(d1>d0) return -1;
		if(d0>d1) return 1;
		return 0;
	}
	
	@Override
	public boolean equals(Object other)
	{
		if (!(other instanceof Point3D)) 
		{
            return false;
        }
		return equals((Point3D)other);
	}
	
	public boolean equals(Point3D src)
	{
		double d = Math.abs(distance(src));
		boolean res = false;
		res = (d < EPSILON);
	    //res = X() == src.X() && Y() == src.Y() && Z() == src.Z();
		//System.out.println("Comp: " + infoI() + (res ? "==":"!=") + src.infoI());
		return res;
	}

	public Point3D add(Point3D other)
	{
		Point3D result = this;
		result.m_x += other.x();
		result.m_y += other.y();
		result.m_z += other.z();
		result.m_t += other.t();
		
		return result;
	}
	
	public boolean equalsXY(Point3D src)
	{
		return Math.abs(distanceXY(src)) < EPSILON;
		//return X() == src.X() && Y() == src.Y();
		
	}
	public String info()
	{
		return "(" + m_x + "," + m_y + "," + m_z + ") time: " + m_t;
	} 
	
	public String infoI()
	{
		return "(" + X() + "," + Y() + "," + X() + ") time: " + m_t;
	}
	
	public void show()
	{
		System.out.println(info());
	}
	
	public double lengthSquared() 
	{
		return x()*x() + y()*y() + z()*z();
	}
	public double length() 
	{
		return (double)Math.sqrt( lengthSquared() );
	}

	public Point3D negated() 
	{
		return new Point3D(-x(),-y(),-z(), -t());
	}

	public Point3D normalized() 
	{
		double l = length();
		if ( l > 0 ) 
		{
			double k = 1/l; // scale factor
			return new Point3D(k*x(),k*y(),k*z(),t());
		}
		else
		{
			return new Point3D(x(),y(),z(),t());
		}
	}

	// returns the dot-product of the given vectors
	static public double dot( Point3D a, Point3D b ) 
	{
		return a.x()*b.x() + a.y()*b.y() + a.z()*b.z();
	}

	// returns the cross-product of the given vectors
	static public Point3D cross( Point3D a, Point3D b ) 
	{
		return new Point3D(
			a.y()*b.z() - a.z()*b.y(),
			a.z()*b.x() - a.x()*b.z(),
			a.x()*b.y() - a.y()*b.x()
		);
	}

	// returns the sum of the given vectors
	static public Point3D sum( Point3D a, Point3D b ) 
	{
		return new Point3D( a.x()+b.x(), a.y()+b.y(), a.z()+b.z(), a.t()+b.t() );
	}

	// returns the difference of the given vectors
	static public Point3D diff( Point3D a, Point3D b ) 
	{
		return new Point3D( a.x()-b.x(), a.y()-b.y(), a.z()-b.z(),a.t()-b.t() );
	}

	// returns the product of the given vector and scalar
	static public Point3D mult( Point3D a, double b ) 
	{
		return new Point3D( a.x()*b, a.y()*b, a.z()*b, a.t()*b );
	}

	// Returns the angle, in [-pi,pi], between the two given vectors,
	// and whose sign corresponds to the right-handed rotation around
	// the given axis to get from v1 to v2.
	static public double computeSignedAngle( Point3D v1, Point3D v2, 
			Point3D axisOfRotation ) 
	{

		Point3D crossProduct = Point3D.cross( v1.normalized(), v2.normalized() );

		// Due to numerical inaccuracies, the length of the cross product
		// may be slightly more than 1.
		// Calling arcsin on such a value would result in NaN.
		double lengthOfCross = crossProduct.length();
		double angle = ( lengthOfCross >= 1 ) ? (double)Math.PI/2 : (double)Math.asin( lengthOfCross );

		if ( Point3D.dot( v1, v2 ) < 0 )
		{
			angle = (double)Math.PI - angle;
		}
		if ( Point3D.dot( crossProduct, axisOfRotation ) < 0 )
		{
			angle = -angle;
		}
		return angle;
	}
	
	public Point3D symX()
	{
		Point3D res = copy();
		res.m_x = -m_x;
		return res;
	}

	public Point3D symY()
	{
		Point3D res = copy();
		res.m_y = -m_y;
		return res;
	}

	public Point3D symZ()
	{
		Point3D res = copy();
		res.m_z = -m_z;
		return res;
	}

	public Point3D symT()
	{
		Point3D res = copy();
		res.m_t = -m_t;
		return res;
	}

	public void floor() 
	{
		m_x = m_x < 0 ? 0.0 : m_x;
		m_y = m_y < 0 ? 0.0 : m_y;
		m_z = m_z < 0 ? 0.0 : m_z;
		m_t = m_t < 0 ? 0.0 : m_t;
	}

	public Point3D ground() 
	{
		Point3D res = copy();
		res.m_z = 0.0;
		return res;
	}
}
