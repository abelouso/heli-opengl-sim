//-*-java-*-
// Copyright 2015, Dan and Sasha
//

package org.heli;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Graphics;

import javax.swing.JPanel;

public class DanookHUD extends JPanel {

	private double fuelCapacity;
	private double fuelLevel;
	
    public DanookHUD(double totalFuel)
    {
        super();
        fuelCapacity = totalFuel;
        fuelLevel = fuelCapacity;
        setPreferredSize(new Dimension(20,100));
    }

    public void setFuelLevel(double newFuel)
    {
    	fuelLevel = newFuel;
    	this.repaint();
    }
    
	 @Override
	    public void paintComponent(Graphics g) {
	        super.paintComponent(g);

	        int totalWidth = getWidth();
	        int totalHeight = getHeight();
	        double fuelRatio = fuelLevel / fuelCapacity;
	        int fuelWidth = (int)(fuelRatio * (double)totalWidth);
	        g.drawRect(0,0,totalWidth,totalHeight);
	        g.setColor(Color.blue);;
	        g.fillRect(0,0,fuelWidth, totalHeight);
	    }
}
