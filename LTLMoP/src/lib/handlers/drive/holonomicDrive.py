#!/usr/bin/env python
"""
=======================================================
holonomicDrive.py - Ideal Holonomic Point Drive Handler
=======================================================

Passes velocity requests directly through.
Used for ideal holonomic point robots.
"""

class driveHandler:
    def __init__(self, proj, shared_data,multiplier,maxspeed):
        """
        Passes velocity requests directly through.
        Used for ideal holonomic point robots.
        
        multiplier (float): Scale the velocity from motionControlHandler (default=1.0,min=1.0,max=50.0)
        maxspeed (float): Max speed allowed (default=999.0)
        """
        try:
            self.loco = proj.h_instance['locomotionCommand']
            self.coordmap = proj.coordmap_lab2map
        except NameError:
            print "(DRIVE) Locomotion Command Handler not found."
            exit(-1)

        self.mul = multiplier
        self.max = maxspeed

    def setVelocity(self, x, y, theta=0):
        x = min(x*self.mul,self.max)
        y = min(y*self.mul,self.max)
        
        #print "VEL:%f,%f" % tuple(self.coordmap([x, y]))
        self.loco.sendCommand([x,y])

