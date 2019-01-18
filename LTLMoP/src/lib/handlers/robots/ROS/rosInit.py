
#!/usr/bin/env python
"""
=================================================
rosSim.py - ROS/Gazebo Initialization Handler
=================================================
"""
import math
import roslib; roslib.load_manifest('gazebo')
import sys, subprocess, os, time, os, shutil, rospy
import cairo, rsvg
import re, Polygon, Polygon.IO
import lib.regions as regions
#import execute
from numpy import *
#from gazebo.srv import *
from gazebo_msgs.srv import *
from gazebo import gazebo_interface
from gazebo_msgs.msg import ModelState
from geometry_msgs.msg import Pose
from geometry_msgs.msg import Twist
import fileinput

class initHandler:
    def __init__(self, proj, init_region, worldFile='ltlmop_map.world', robotPixelWidth=200, robotPhysicalWidth=.5, robotPackage="pr2_gazebo", robotLaunchFile="pr2.launch", modelName = "pr2", calib=False):
        """
        Initialization handler for ROS and gazebo

        init_region (region): The initial region of the robot
        worldFile (str): The alternate world launch file to be used (default="ltlmop_map.world")
        robotPixelWidth (int): The width of the robot in pixels in ltlmop (default=200)
        robotPhysicalWidth (float): The physical width of the robot in meters (default=.5)
        robotPackage (str): The package where the robot is located (default="pr2_gazebo")
        robotLaunchFile (str): The launch file name for the robot in the package (default="pr2.launch")
        modelName(str): Name of the robot. Choices: pr2 and quadrotor for now(default="pr2")
        """

        #Set a blank offset for moving the map
        self.offset=[0,0]
        #The package and launch file for the robot that is being used        
        self.package=robotPackage
        self.launchFile=robotLaunchFile
        #The world file that is to be launched, see gazebo_worlds/worlds
        self.worldFile=worldFile
        #Map to real world scaling constant
        self.ratio= robotPhysicalWidth/robotPixelWidth
        self.robotPhysicalWidth = robotPhysicalWidth
        self.modelName          = modelName 
        self.coordmap_map2lab   = proj.coordmap_map2lab   
        addObstacle = False            
        
        # change the starting pose of the box
        self.original_regions = proj.loadRegionFile()
        self.destination="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/"+self.worldFile 
        self.state      ="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_state.world" 
        #clean the original file for world and state
        f = open(self.destination,"w")
        f.close()
        f = open(self.state,"w")
        f.close()
        
        # start the world file with the necessities
        source="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_essential_front.world"
        self.appendObject(source,self.destination)
        
        if self.worldFile=='ltlmop_map.world':
            #This creates a png copy of the regions to load into gazebo
            self.createRegionMap(proj)
        #Change robot and world file in gazebo:
        self.changeRobotAndWorld(proj)
        
        # close the world file with the necessities
        source="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_essential_end.world"
        self.appendObject(source,self.destination)
        
        # Center the robot in the init region (not on calibration)
        if not init_region=="__origin__" :
            self.centerTheRobot(proj, init_region)
            
            #clean the original file for world and state
            f = open(self.destination,"w")
            f.close()
            f = open(self.state,"w")
            f.close()
            
            # start the world file with the necessities
            source="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_essential_front.world"
            self.appendObject(source,self.destination)
            
            if self.worldFile=='ltlmop_map.world':
                #This creates a png copy of the regions to load into gazebo
                self.createRegionMap(proj)
            #Change robot and world file in gazebo:
            self.changeRobotAndWorld(proj)
            
            # check if there are obstacles. If so, they will be added to the world
            for region in self.original_regions.regions:
                if region.isObstacle is True:
                    addObstacle = True   
                    break
            
            source="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_essential_state.world"
            self.appendObject(source,self.state)
        
            if addObstacle is False:
                print "INIT:NO obstacle"                  
            
            if addObstacle is True:
                print "INIT:OBSTACLES!!" 
                # start the ltlmop_state.world file with the necessities
                
                i = 0
                ######### ADDED
                self.proj = proj
                self.map = {'polygon':{},'original_name':{},'height':{}}
                for region in self.proj.rfi.regions:
                    self.map['polygon'][region.name] = self.createRegionPolygon(region)
                    for n in range(len(region.holeList)): # no of holes
                        self.map['polygon'][region.name] -= self.createRegionPolygon(region,n)
                
                ###########
                for region in self.original_regions.regions:                                
                    if region.isObstacle is True:                                
                        poly_region = self.createRegionPolygon(region)
                        center = poly_region.center()
                        print >>sys.__stdout__,"center:" +str(center)
                        pose = self.coordmap_map2lab(region.getCenter())
                        print >>sys.__stdout__,"pose:" + str(pose)
                        pose = center
                        height = region.height
                        if height == 0:
                            height = self.original_regions.getMaximumHeight()
                        
                        """
                        #Fina the height and width of the region
                        pointArray = [x for x in region.getPoints()]
                        pointArray = map(self.coordmap_map2lab, pointArray)
                        # Find how much our bounding box has shifted in relation to the old one
                        for j, pt in enumerate(pointArray):
                            if j == 0:
                                # Set initial values
                                topLeftX  = pt[0]
                                topLeftY  = pt[1]
                                botRightX = pt[0]
                                botRightY = pt[1]
                            else:
                                # Check for any points that would expand our bounds
                                if pt[0] > botRightX:
                                    botRightX = pt[0]
                                if pt[0] < topLeftX:
                                    topLeftX = pt[0]
                                if pt[1] < topLeftY:
                                    topLeftY = pt[1]
                                if pt[1] > botRightY:
                                    botRightY = pt[1]
                    
                        
                        size = [botRightX - topLeftX, botRightY - topLeftY]
                        """
                        
                        a = poly_region.boundingBox()
                        size = [a[1]-a[0],a[3]-a[2]] #xmax,xmin,ymax,ymin
                                    
                        if "pillar" in region.name.lower():    # cylinders
                           radius = min(size[0],size[1])/2
                           print "INIT: pose "+str(pose)+" height: "+str(height)+" radius: "+str(radius)
                           self.addCylinder(i,radius,height,pose)
                        else:         
                            length= size[0]   #width in region.py = size[0]
                            depth= size[1]  #height in region.py =size[1]
                            print "INIT: pose "+str(pose)+" height: "+str(height)+" length: "+str(length)+" depth: "+str(depth)
                            self.addBox(i,length,depth,height,pose)
                        i += 1
                
            #append ltlmop_state.world to worldfile
            self.appendObject(self.state,self.destination)
            
            # close the world file with the necessities
            source="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_essential_end.world"
            self.appendObject(source,self.destination)
            
        # set up a publisher to publish pose
        self.pub = rospy.Publisher('/gazebo/set_model_state', ModelState)
        
        # Create a subprocess for ROS
        self.rosSubProcess(proj)

        #The following is a global node for LTLMoP
        rospy.init_node('LTLMoPHandlers')    
    
    def createRegionPolygon(self,region,hole = None):
        """
        This function takes in the region points and make it a Polygon.
        """
        if hole == None:
            pointArray = [x for x in region.getPoints()]
        else:
            pointArray = [x for x in region.getPoints(hole_id = hole)]
        pointArray = map(self.coordmap_map2lab, pointArray)
        regionPoints = [(pt[0],pt[1]) for pt in pointArray]
        formedPolygon= Polygon.Polygon(regionPoints)
        return formedPolygon
    
    def addBox(self,i,length,depth , height, pose):
        """
        to add a cylinder into the world
        i = count for the name  (just to distinguish one model from another)
        length = length of the box (in x direction)
        depth  = depth of the box  (in y direction)
        height = height of the cylinder
        pose   = center of the cylinder
        """
        # for editing the starting pose of the cylinder (box works the same way)
        # change the name of the model
        path="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_box.world"
        searchExp='<model name='
        replaceExp='<model name="box_model_'+str(i)+'" static="1">\n'
        self.replaceAll(path,searchExp,replaceExp)
        
        searchExp='<link name='
        replaceExp='      <origin pose="0.000000 0.000000 '+str(float(height)/2)+' 0 -0.000000 0.000000"/>\n'
        self.replaceNextLine(path,searchExp,replaceExp)
        
        # change the pose of the model
        searchExp='    </link>'
        replaceExp='    <origin pose="'+str(pose[0])+' '+str(pose[1])+' 0 0 0 0 " />\n'
        self.replaceNextLine(path,searchExp,replaceExp)
        
        # change the radius and height of the model
        searchExp='<box size='
        replaceExp='       <box size="'+str(length)+' '+str(depth)+' '+str(height)+'"/>\n'
        self.replaceAll(path,searchExp,replaceExp)
        
        #append to the world file
        self.appendObject(path,self.destination)
        
        # change the state file for cylinder
        path="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_state_cylinder.world"
        searchExp='    <model name='
        replaceExp='    <model name="box_model_'+str(i)+'">\n'
        self.replaceAll(path,searchExp,replaceExp)
        
        searchExp='    <model name='
        replaceExp='      <pose>'+str(pose[0])+' '+str(pose[1])+' 0 0 0 0 </pose>\n'
        self.replaceNextLine(path,searchExp,replaceExp)
        
        searchExp='<link name='
        replaceExp='      <pose>0 0 0 0 0 0 </pose>\n'
        self.replaceNextLine(path,searchExp,replaceExp)
        
        #append to the state file
        self.appendObject(path,self.state)
        
    def addCylinder(self,i,radius, height, pose):
        """
        to add a cylinder into the world
        i = count for the name  (just to distinguish one model from another)
        radius = radius of the cylinder
        height = height of the cylinder
        pose   = center of the cylinder
        """
        # for editing the starting pose of the cylinder (box works the same way)
        # change the name of the model
        path="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_cylinder.world"
        searchExp='<model name='
        replaceExp='<model name="cylinder_'+str(i)+'" static="1">\n'
        self.replaceAll(path,searchExp,replaceExp)
        
        # change the pose of the model
        searchExp='    </link>'
        replaceExp='    <origin pose="'+str(pose[0])+' '+str(pose[1])+' 0 0 0 0 " />\n'
        self.replaceNextLine(path,searchExp,replaceExp)
        
        # change the radius and height of the model
        searchExp='<cylinder radius='
        replaceExp='       <cylinder radius="'+ str(radius)+'" length="'+str(height)+'"/>\n'
        self.replaceAll(path,searchExp,replaceExp)
        
        #append to the world file
        self.appendObject(path,self.destination)
        
        # change the state file for cylinder
        path="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_state_cylinder.world"
        searchExp='    <model name='
        replaceExp='    <model name="cylinder_'+str(i)+'">\n'
        self.replaceAll(path,searchExp,replaceExp)
        
        searchExp='    <model name='
        replaceExp='      <pose>'+str(pose[0])+' '+str(pose[1])+' 0 0 0 0 </pose>\n'
        self.replaceNextLine(path,searchExp,replaceExp)
        
        searchExp='<link name='
        replaceExp='      <pose>0 0 '+str(float(height)/2)+' 0 0 0 </pose>\n'
        self.replaceNextLine(path,searchExp,replaceExp)
        
        #append to the state file
        self.appendObject(path,self.state)

    def replaceNextLine(self,file,searchExp,replaceExp):
        """
        Relaces lines in a file given a search string and replacement string
        You only need a portion of the line to match the searchExp and 
        then it will replace the whole line with the replaceExp
        """
        found = False
        done  = False
        for line in fileinput.input(file, inplace=1):
            
            if found is True:
                done = True
                found = False
                #print line
                #print "replace"
                line = line.replace(line,replaceExp)

            if searchExp in line and done is False:
                found = True
                
            sys.stdout.write(line)
    
    def appendObject(self,source, dest):
        """
        append lines from source file to destination file
        source: source file
        dest  : destination file
        """
        myfile = open(source,"r")
        #with open(source,"r") as myfile:
        f=open(dest,"a") ## file open in appending mode i.e 'a'
        for line in myfile:
            f.write(line)
        f.close() ## File closing after writingself.
        myfile.close()
            
    def getSharedData(self):
        # TODO: Return a dictionary of any objects that will need to be shared with other handlers
        return {'ROS_INIT_HANDLER': self}

    def region2svg(self, proj, regionFile):
        """
        Converts region file to svg
        This is from the deprecated regions file with slight changes for 
        proper calculation of the size of the regions map
        """
        fout=re.sub(r"\.region$", ".svg", regionFile)
        rfi = regions.RegionFileInterface()
        rfi.readFile(regionFile)

        polyList = []
        
        for region in rfi.regions:
            points = [(pt.x,-pt.y) for pt in region.getPoints()]
            poly = Polygon.Polygon(points)
            polyList.append(poly)
        try: #Normal Operation
            boundary=proj.rfiold.regions[proj.rfiold.indexOfRegionWithName("boundary")]
        except: #Calibration
            boundary=proj.rfi.regions[proj.rfi.indexOfRegionWithName("boundary")]
        width=boundary.size.width
        height=boundary.size.height

        #use boundary size for image size
        #Polygon.IO.writeSVG(fout, polyList,width=width,height=height)
        Polygon.IO.writeSVG(fout, polyList,width=height,height=width)   # works better than width=width,height=height


        return fout #return the file name

    def replaceAll(self,file,searchExp,replaceExp):
        """
        Relaces lines in a file given a search string and replacement string
        You only need a portion of the line to match the searchExp and 
        then it will replace the whole line with the replaceExp
        """
        for line in fileinput.input(file, inplace=1):
            if searchExp in line:
                line = line.replace(line,replaceExp)
            sys.stdout.write(line)

    def createRegionMap(self, proj):
        """
        This function creates the ltlmop region map as a floor plan in the 
        Gazebo Simulator.
        """
        #This block creates a copy and converts to svg
        texture_dir =  '/opt/ros/fuerte/stacks/simulator_gazebo/gazebo/gazebo/share/gazebo-1.0.2/Media/materials/textures' #potentially dangerous as pathd in ROS change with updates
        ltlmop_path = proj.getFilenamePrefix()
        regionsFile = ltlmop_path+"_copy.regions"
        shutil.copy(proj.rfi.filename,regionsFile)
        svgFile = self.region2svg(proj, regionsFile)
        svg = rsvg.Handle(file=svgFile)
        
        #This block converts the svg to png and applies naming conventions
        self.imgWidth=svg.props.width
        self.imgHeight=svg.props.height
        img = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.imgWidth, self.imgHeight)
        ctx = cairo.Context(img)
        handler = rsvg.Handle(svgFile)
        handler.render_cairo(ctx)
        img.write_to_png(ltlmop_path+"_simbg.png")
        ltlmop_map_path = ltlmop_path + "_simbg.png"
        shutil.copy (ltlmop_map_path, texture_dir)
        full_pic_path = texture_dir + "/" + proj.project_basename + "_simbg.png"
        shutil.copyfile (full_pic_path, (texture_dir + "/" + 'ltlmop_map.png'))
        
        # Change size of region map in gazebo
        # This is accomplished through edits of the world file before opening
        path="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/"+self.worldFile # Potential problem when version changes >_<
        #path="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/worlds/ltlmop_map.world" # Potential problem when version changes >_<
        searchExp='<box size='
        T=[self.ratio*self.imgWidth,self.ratio*self.imgHeight]
        resizeX=T[0]
        resizeY=T[1]
        replaceExp='            <box size="'+str(resizeX)+' '+str(resizeY)+' .1" />\n'
        self.replaceAll(path,searchExp,replaceExp)

    def changeRobotAndWorld(self, proj):
        """
        This changes the robot in the launch file
        """
        #Accomplish through edits in the launch file
        path="/opt/ros/fuerte/stacks/simulator_gazebo/gazebo_worlds/launch/ltlmop.launch"
        searchExp='<include file='
        replaceExp='    <include file="$(find '+self.package+')/launch/'+self.launchFile+'" />\n'
        self.replaceAll(path,searchExp,replaceExp)
        
        
        searchExp='<node name="gazebo" pkg="gazebo"'
        replaceExp='    <node name="gazebo" pkg="gazebo" type="gazebo" args=" $(find gazebo_worlds)/worlds/'+self.worldFile+'" respawn="false" output="screen"/>\n'
        self.replaceAll(path,searchExp,replaceExp)


    def rosSubProcess(self, proj, worldFile='ltlmop_map.world'):  
        start = subprocess.Popen(['roslaunch gazebo_worlds ltlmop.launch'], shell = True, stdout=subprocess.PIPE)
        start_output = start.stdout
        

        # Wait for it to fully start up
        while 1:
            input = start_output.readline()
            print input, # Pass it on
            if input == '': # EOF
                print "(INIT) WARNING:  Gazebo seems to have died!"
                break
            if "Successfully spawned" or "successfully spawned" in input:
                #Successfully spawend is output from the creation of the PR2
                #It might get stuck waiting for another type of robot to spawn
                time.sleep(5)
                break

    def centerTheRobot(self, proj, init_region):
        # Start in the center of the defined initial region
        
        try: #Normal operation
            initial_region = proj.rfiold.regions[proj.rfiold.indexOfRegionWithName(init_region)]
        except: #Calibration
            initial_region = proj.rfi.regions[proj.rfi.indexOfRegionWithName(init_region)]
        center = initial_region.getCenter()
    
        # Load the map calibration data and the region file data to feed to the simulator
        coordmap_map2lab,coordmap_lab2map = proj.getCoordMaps()
        map2lab = list(coordmap_map2lab(array(center)))

        print "Initial region name: ", initial_region.name, " I think I am here: ", map2lab, " and center is: ", center

        os.environ['ROBOT_INITIAL_POSE']="-x "+str(map2lab[0])+" -y "+str(map2lab[1])
