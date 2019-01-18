#!/usr/bin/env python
"""
================================================================================
pioneerExampleLocomotionCommand.py - Pioneer Locomotion Command Handler
================================================================================
"""
import socket, sys, time


class locomotionCommandHandler:
    def __init__(self, proj, shared_data):
        try:
            self.robocomm = shared_data['robocomm']
        except KeyError, ValueError:
            print "(LOCO) ERROR: No RobotCommunicator set to key 'robocomm' in shared data from init."
            exit(-1)
    
    def sendCommand(self, cmd):
        # Command the robot based on the gait given by the drive handler.
        direction = (cmd[0],cmd[1])
        self.robocomm.sendDirection(direction)
        #if cmd[0]==0.0:
        #    time.sleep(0.1)
