package org.heli;

/** Chopper Aggregator, Copyright 2015, Dan and Sasha
 * 
 * @author Daniel LaFuze
 *
 */

/** This class is just for convenience so the world doesn't have to
 * keep track of all of this stuff manually
 * @author Daniel
 *
 */
public class ChopperAggregator {
	private StigChopper theChopper;
	private ChopperInfo chopInfo;
	
	// Define constants in here that are needed in both StigChopper and ChopperInfo
	public static final double BASE_MASS = 100.0; // kg
	
	// Total Capacity can be divided however desired between cargo and fuel
	public static final double TOTAL_CAPACITY = 300.0; // kg
	
	public static final double ITEM_WEIGHT = 10.0;
	
	public ChopperAggregator(StigChopper chop, ChopperInfo inf) {
		theChopper = chop;
		chopInfo = inf;
	}

	public StigChopper getChopper() { return theChopper; }
	
	public ChopperInfo getInfo() { return chopInfo; }
}
