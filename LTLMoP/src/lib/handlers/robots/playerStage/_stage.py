#!/usr/bin/env python
"""
==================================================
stage.py - Stage Simulation Initialization Handler
==================================================

Create config files for Stage and start it up (as part of a player server) in a subprocess
"""

import textwrap, os, subprocess, time, sys
from numpy import *
from copy import deepcopy

INSIDE_ANOTHER_WX_APP = ('wx' in sys.modules)

import wx
import regions
reload(regions) # to use wx objects
import mapRenderer

class initHandler:
    def __init__(self, proj, init_region):
        """
        If ``init_region`` is ``__origin__``, we'll start the robot at location ``(0, 0)``.

        Otherwise, it will begin in the center of the defined initial region.
        """

        self.proj = proj 

        ### Create Stage config files
        self.init_region = init_region
        print "(INIT) Writing Stage configuration files..."
        self.writeSimConfig(proj)

        ### Start Stage (Player server)

        print "(INIT) Starting Stage (Player server)..."
        print "=============================================="

        # Create a subprocess
        p_player = subprocess.Popen(["player", proj.getFilenamePrefix() + ".cfg"], stdout=subprocess.PIPE)
        fd_player = p_player.stdout
        
        # Wait for it to fully start up
        while 1:
            input = fd_player.readline()
            print input, # Pass it on
            if input == '': # EOF
                print "(INIT) WARNING: Player seems to have died!"
                break
            if "Stage driver creating 1 device" in input:
                # NOTE: I'd prefer to wait for "Listening on ports" but it's buffered so we never get it until Stage quits
                # We'll just have to wait for a moment after this to be sure
                time.sleep(1)
                print "=============================================="
                print "OK! Looks like Stage is at least mostly alive."
                # TODO: Better handling of error cases
                break

    def getSharedData(self):
        """ Returns nothing """
        return {}  # We have nothing to share
         
    def makeBackgroundImage(self):
        """
        Write out a png file with the regions.
        Returns the output filename.
        """

        # We need to have a wx.App instance to use the wx drawing stuff
        if not INSIDE_ANOTHER_WX_APP:
            app = wx.App()
            wx.InitAllImageHandlers()
        else:
            app = None

        bitmap = wx.EmptyBitmap(640,480)
        temp_rfi = deepcopy(self.proj.rfi)

        # Set all colors to white because stage background is B/W
        for r in temp_rfi.regions:
            r.color.SetFromName('WHITE')

        # Remove boundary
        i = temp_rfi.indexOfRegionWithName('boundary')
        if i >= 0: temp_rfi.regions.pop(i)
        
        mapRenderer.drawMap(bitmap, temp_rfi, memory=True, highlightList=[r.name for r in temp_rfi.regions])
        fname = self.proj.getFilenamePrefix() + "_simbg.png"
        bitmap.SaveFile(fname, wx.BITMAP_TYPE_PNG)

        if app is not None:
            app.Destroy()

        return fname

    def writeSimConfig(self, proj):
        """
        Generates .world and .cfg files for Stage.
        """

        # Choose starting position
        calib = (self.init_region == '__origin__')
        
        if calib:
            # Seems like a reasonable place to start, no?
            startpos = array([0,0])
        else:
            # Start in the center of the defined initial region
            for i,r in enumerate(proj.rfiold.regions):
                if r.name == self.init_region:
                    initial_region = r
                    break
            initial_region = proj.rfi.regions[proj.rfi.indexOfRegionWithName(proj.regionMapping[initial_region.name][0])]
            startpos = proj.coordmap_map2lab(initial_region.getCenter())

        # Create an appropriate background image

        bgFile = self.makeBackgroundImage()
        #bgFile = proj.getFilenamePrefix()+"_simbg.png"

        ####################
        # Stage world file #
        ####################

        f_world = open(proj.getFilenamePrefix() + ".world", "w")

        f_world.write(textwrap.dedent("""
            # Just a really simple robot abstraction
            define pointbot position
            (
                # Actual size
                size [0.33 0.33]

                # Show the front
                gui_nose 1

                # Just a silly box
                polygons 1
                polygon[0].points 4
                polygon[0].point[0] [  0  0 ]
                polygon[0].point[1] [  0  1 ]
                polygon[0].point[2] [  1  1 ]
                polygon[0].point[3] [  1  0 ]

                # Simplify as holonomic robot
                drive "omni"
            )

            # Defines "map" object used for floorplans
            define map model
            (
                color "black"

                # most maps will need a bounding box
                boundary 1

                gui_nose 0
                gui_grid 1
                gui_movemask 0
                gui_outline 0

                gripper_return 0
            )

            # size of the world in meters
            size [16 12]

            # set the resolution of the underlying raytrace model in meters
            resolution 0.02

            # update the screen every 10ms 
            gui_interval 20

            # configure the GUI window
            window
            (
                size [ 591.000 638.000 ]
                center [0 0]
                scale 0.028
            )

            # load an environment bitmap
            map
            (
                bitmap "%s"
                size [16 12]
                name "example1"
                boundary 0
                obstacle_return 0
            )

            # create a robot
            pointbot
            (
                name "robot1"
                color "red"
                pose [%f %f 0]

                localization "gps"
                localization_origin [0 0 0]
            )
                """ % (bgFile, startpos[0], startpos[1])))

        if calib:
            # Add little (moveable) boxes at region vertices to test calibration
            f_world.write(textwrap.dedent("""          
                define puck model(
                size [ 0.08 0.08 ]
                gripper_return 1
                gui_movemask 3
                gui_nose 0
                )
            """))

            pts = []
            for region in proj.rfi.regions:
                for pt in region.getPoints():
                    if pt not in pts: # Only draw shared vertices once!
                        f_world.write("puck( pose [%f %f 0.0 ] color \"red\" )\n" % tuple(proj.coordmap_map2lab(pt)))
                        pts.append(pt)

        f_world.close()

        ############################
        # Stage configuration file #
        ############################

        f_cfg = open(proj.getFilenamePrefix() + ".cfg", "w")

        f_cfg.write(textwrap.dedent("""
            # Load the Stage plugin simulation driver
            driver
            (
            name "stage"
            provides ["simulation:0" ]
            plugin "libstageplugin"

            # load the named file into the simulator
            worldfile "%s.world"
            )

            driver
            (
            name "stage"
            provides ["map:0"]
            model "example1"
            )

            # Create a Stage driver and attach position2d interfaces 
            # to the model "robot1"
            driver
            (
            name "stage"
            provides ["position2d:0"]
            model "robot1"
            )
        """ % proj.getFilenamePrefix()))

        f_cfg.close()
