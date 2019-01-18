#!/usr/bin/env python
"""
==========================================================
NullPose.py - Pose Handler for single region without Vicon
==========================================================
"""

import sys, time
from numpy import *
from regions import *

class poseHandler:
    def __init__(self, proj, shared_data, initial_region):
        """
        Null pose handler - used for single region operation without Vicon
        
        initial_region (region): Starting position for robot
        """
        
        r = proj.rfiold.indexOfRegionWithName(initial_region)
        center = proj.rfiold.regions[r].getCenter()
        self.x = center[0]
        self.y = center[1]
        self.theta = 0

    def getPose(self, cached=False):
        
        x=self.x
        y=self.y
        o=self.theta

        return array([x, y, o])
        
    def setPose(self, x, y, theta):
        self.x=x
        self.y=y
        self.theta=theta
        
