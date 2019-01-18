#!/usr/bin/env python

import numpy as np
from copy import deepcopy

from gazebo_world import *
from tf.transformations import euler_from_quaternion

from automaton import Node, Automaton, AutomatonSynthesizer
from map import MapRegion, Map
from widget import Widget

class SimObject(object):
	def __init__(self, world, name, objtype = ""):
		"""
		Create an object and spawn it in the Gazebo simulation.

		params:
		world:        world to which the object belongs to
		name:         name of the object (e.g. 'bomb1', hostage3')
		sdf_filepath: path to sdf model file
		initial_position:     position of the object (e.g. [0.5, 2.0, 0.0])
		initial_orientation:  orientation of object in rad (e.g. [0.0, 1.58, numpy.pi])
		objtype:      type of object, ('hostage' or 'bomb' or 'robot') 
		"""
		if not isinstance(world, GazeboWorld):
			raise Exception("World must be an instance of GazeboWorld.")

		self.world = world
		self.name = name
		self.objtype = objtype
		self.model = None

	def get_name(self):
		return self.name

	def get_model(self):
		return self.model

	def get_type(self):
		return self.objtype

class StaticObject(SimObject):
	"""A static object, e.g. bomb or hostage"""
	def __init__(self, world, name, sdf_filepath, 
		         initial_position, initial_orientation, objtype=""):
		super(StaticObject, self).__init__(world, name, objtype)
		self.position = initial_position
		self.orientation = initial_orientation
		#Create a model for this object
		self.model = GazeboModel(name, sdf_filepath = sdf_filepath)
		#Spawn this object in the Gazebo world to make it visible
		self.world.spawn_model(self.model, self.position, self.orientation)
		#Assign a relative entity to the object's model
		entities = self.world.get_model_entities(self.model.name)
		self.model.set_relative_entity_name(entities[0]) #pick 1st entity in the list

		self.close_point = None

	def get_pose(self):
		"""Return position and orientation of object"""
		return self.position, self.orientation

	def get_close_point(self):
		return self.close_point

	def set_close_point(self, point):
		self.close_point = point

class Robot(SimObject):
	"""A moving object, i.e. the robot."""
	def __init__(self, world, map, objtype = "robot", sensors = [], actuators = []):
		"""
		params:
		actuators: list of actions that robot can execute
		           e.g. ['defuse', 'interact']
		sensors:   list of objects that robot can sense
		           e.g. ['bomb', 'hostage']
		"""
		super(Robot, self).__init__(world, "mobile_base", objtype)
		#turtlebot model should be spawned when we launch gazebo
		#thus we only have to look for it among the spawned models
		if "mobile_base" in self.world.get_model_names():
			entities = self.world.get_model_entities("mobile_base")
			self.model = GazeboModel("mobile_base", entities[0])
		else:
			raise Exception("ERROR: Robot model is not spawned in the world. ")
        
		self.map = map
		self.actuators = [] #actions that robot can execute, e.g. ["defuse", "interact"]
		self.sensors = []   #objects that robot can sense, e.g. ["bomb", "hostage"]
		self.state = None

	def add_sensor(self, sensor):
		if not isinstance(sensor, str):
			raise Exception("Sensor must be specified as a string.")
		if not sensor in self.sensors:
			self.sensors.append(sensor)

	def add_actuator(self, actuator):
		if not isinstance(actuator, str):
			raise Exception("Actuator must be specified as a string")
		if not actuator in self.actuators:
			self.actuators.append(actuator)

	def set_sensors(self, sensors_list):
		self.sensors = sensors_list

	def set_actuators(self, act_list):
		self.actuators = act_list

	def get_state(self):
		return self.state

	def set_state(self, sensor_props, act_props, react_props, goal_props, region):
		"""
		Set the state of the robot.
		params:
        sensor_props: list of tuples with sensor propositions
                      and their truth value.
                      e.g. [('bomb', True), ('hostage', False)]
        act_props:    list of tuples with actuator propositions
                      and their truth value.
                      e.g. [('defuse', True), ('interact', False)]
        react_props:  list of tuples with reaction propositions
                      and their truth value.
                      e.g. [('react_bomb', True), ('react_hostage', False)]
        goal_props:   list of tuples with gaol propositions
                      and their truth value.
                      e.g. [('mem_visit_hall', True), ('mem_visit_corridor', False)]
        region:       current region where the robot is
                      e.g. "hall"
        """
		for (prop, truth) in sensor_props:
			if not prop in self.sensors:
				raise Exception("ERROR: sensor '{}' is not supported by the robot".format(prop))
		for (prop, truth) in act_props:
			if not prop in self.actuators:
				raise Exception("ERROR: action '{}' is not supported by the robot".format(prop))
		self.state = Node(None, sensor_props, react_props, act_props, goal_props, region)

	def get_pose(self):
		"""Return position and orientation of robot in the map"""
		state = self.world.get_robot_amcl_pose()
		position = [state.pose.pose.position.x, state.pose.pose.position.y, state.pose.pose.position.z]
		numpy_orientation = euler_from_quaternion([state.pose.pose.orientation.x, state.pose.pose.orientation.y,
		               state.pose.pose.orientation.z, state.pose.pose.orientation.w])
		orientation = [numpy_orientation[0], numpy_orientation[1], numpy_orientation[2]]
		return position, orientation

	def go_to(self, position, orientation = [0.0, 0.0, 0.0]):
		"""Navigate to the given position and orientation"""
		self.world.navigate_to_goal(position, orientation)

	def do_action(self, act, region, objects, widget, sim_bomb_objects, sim_hostage_objects):
		if not act in self.actuators:
			raise Exception("ERROR: Action '{}' is not supported by the robot.".format(act))
		if act == "defuse":
			for obj in objects:
				if obj.get_type() == "bomb":
					self.do_defuse(obj, region, widget, sim_bomb_objects)
		elif act == "interact":
			for obj in objects:
				if obj.get_type() == "hostage":
					self.do_interact(obj, region, widget, sim_hostage_objects)

	def do_defuse(self, obj, region, widget, sim_bomb_objects):
		"""Defuse a bomb object."""
		#we move closer to the object
		self.go_to(obj.get_close_point())
		#launch message through pop up window
		widget.run_assertion("I am going to defuse the bomb.")
		#delete object and its model from the world
		self.world.delete_model(obj.get_model())
		region.delete_object(obj)
		sim_bomb_objects.remove(obj)

	def do_interact(self, obj, region, widget, sim_hostage_objects):
		"""Interact with a hostage object."""
		#we move closer to the object
		self.go_to(obj.get_close_point())
		#launch message through pop up window
		widget.run_hostage_question(region.get_name(),
									"Are you wounded?.",
									"I'm wounded",
									"I'm fine",
									widget.answer_wounded, 
									widget.answer_fine)
		#delete object and its model from the world
		self.world.delete_model(obj.get_model())
		region.delete_object(obj)
		sim_hostage_objects.remove(obj)

	def has_goals(self):
		"""Return True if robot has goals to pursue."""
		for (prop, truth) in self.state.get_memories():
			if not truth:
				return True
		return False



class Simulator(object):
	def __init__(self, 
		         regions,
		         adjacent_regions,
		         num_bombs,
		         num_hostages,
		         bomb_sdf_filepath,
		         hostage_sdf_filepath):
		"""
		params:
		regions:           dict containing region names as keys and
		                   xmin, xmax, ymin, ymax (i.e. region boundaries)
		                   as values
		adjacent_regions:  list of tuples where each tuple is a pair of adjacent regions
		num_bombs:         number of bombs in the world
		num_hostages:      number of hostages in the world
        bomb_sdf_file:     sdf file for spawning the 3D bomb object model in Gazebo
        hostage_sdf_file:  sdf file for spawning the 3D hostage object modeil in Gazebo
        """
		self.bomb_objects = []
		self.hostage_objects = []
		self.bomb_sdf_filepath = bomb_sdf_filepath
		self.hostage_sdf_filepath = hostage_sdf_filepath
		self.robot = None
		self.world = None
		self.automatons = None
		self.synthesizer = AutomatonSynthesizer()
		self.widget = Widget()

		self.create_world(regions, num_bombs, num_hostages)

	def create_world(self, regions, num_bombs, num_hostages):
		"""Create map and objects."""
		self.world = GazeboWorld()

		#Create Map
		self.map = Map()
		for region_name, boundaries in regions.iteritems():
			region = MapRegion(region_name,
				               boundaries.get('xmin'),
				               boundaries.get('xmax'),
				               boundaries.get('ymin'),
				               boundaries.get('ymax'))
			self.map.add_region(region)
		
		#Create static objects (bombs and hostages) in random regions
		for obj in self.create_objects_randomly_in_map(num_bombs, 
				                                      "bomb", 
				                                      self.bomb_sdf_filepath):
		    self.bomb_objects.append(obj)

		for obj in self.create_objects_randomly_in_map(num_hostages, 
				                                      "hostage", 
				                                      self.hostage_sdf_filepath):
		    self.hostage_objects.append(obj)

		#Create robot
		self.robot = Robot(self.world, self.map)

	def create_objects_randomly_in_map(self, num_obj, obj_type, sdf_filepath):
		"""
		Create an object and add it to a random 
		region of the given map.
		"""
		region_names = self.map.get_region_names()
		objects = []
		for i in range(num_obj):
		    #drawing a random region from the map
		    n = np.random.randint(len(region_names))
		    drawn_name = region_names.pop(n)
		    drawn_region = self.map.get_region(drawn_name)

		    #place the object at a random position within
		    #the drawn region
		    obj_name = obj_type + str(i)
		    obj_position = drawn_region.get_random_point()
		    obj_orientation = [0.0, 0.0, np.random.uniform(-np.pi, np.pi)]
		    obj = StaticObject(self.world, obj_name, sdf_filepath, obj_position, obj_orientation, obj_type)

		    drawn_region.add_object(obj)
		    #Assign a close point to the object, this
		    #will be useful when the robot will have to
		    #approach the object
		    if drawn_region.xmin < 0:
		    		if (obj_position[0] > (drawn_region.xmax + drawn_region.xmin)/2):
		    			x = obj_position[0] - 0.6
		    		else: x = obj_position[0] + 0.6
		    elif drawn_region.xmin > 0:
		    	if (obj_position[0] > drawn_region.xmin + (drawn_region.xmax - drawn_region.xmin)/2):
		    		x = obj_position[0] - 0.6
		    	else: x = obj_position[0] + 0.6
		    obj.set_close_point([x, obj_position[1], 0.0])

		    objects.append(obj)
		return objects

	def run(self, spec_filepath = None, text = ""):
		curr_pos, curr_orient = self.robot.get_pose() #current robot position and orientation
		curr_region = self.map.get_region_from_point(curr_pos) #current region
		new_text = "Start in {}".format(curr_region.get_name()) + text
		spec_chunks = new_text.split('\n')

		#DEBUG
		#print "SPEC TEXT:"
		#print new_text
		#print
		
		num_ifs = 0
		new_spec_chunks = [[]]
		for chunk in spec_chunks:
			if not ("if" in chunk or "If" in chunk):
				for new_chunk in new_spec_chunks:
					new_chunk.append(chunk)
			else:
				num_ifs += 1
				if num_ifs <= 1:
					new_spec_chunks[0].append(chunk)
				else:
					temp_chunk = deepcopy(new_spec_chunks[-1])
					new_chunk = []
					for el in temp_chunk:
						if not ("if" in el or "If" in el):
							new_chunk.append(el)
					new_chunk.append(chunk)
					new_spec_chunks.append(new_chunk)

		#let's process the specification and create the automatons
		self.automatons = []
		for i, spec_list in enumerate(new_spec_chunks):
			spec_text = '\n'.join(spec_list)
			self.automatons.append(self.synthesizer(spec_filepath, spec_text, i))

		#set the enabled actions and sensors for the robot
		#i.e. actions that can be executed and objects that
		#can be sensed by the robot
		for aut in self.automatons:
			for s in aut.get_sensors():
				self.robot.add_sensor(s)
			for a in aut.get_actuators():
				self.robot.add_actuator(a)

		#If objects were made unvisible in previous iteration
		#now we reset them
		for h_obj in self.hostage_objects:
			obj_pos, obj_orient = h_obj.get_pose()
			obj_region = self.map.get_region_from_point(obj_pos)
			if not h_obj in obj_region.get_objects():
				obj_region.add_object(h_obj)

		for b_obj in self.bomb_objects:
			obj_pos, obj_orient = b_obj.get_pose()
			obj_region = self.map.get_region_from_point(obj_pos)
			if not b_obj in obj_region.get_objects():
				obj_region.add_object(b_obj)

		#We define the initial state of the robot for each automaton
		#Note: in the initial state all props are False for the robot
		curr_states = [] #the current states in each automaton
		for aut in self.automatons:
			#propositions in initial state
			act_props = [(act, False) for act in aut.get_actuators()]
			sensor_props = [(sense, False) for sense in aut.get_sensors()]
			react_props = [(react, False) for react in aut.get_reactions()]
			goal_props = [(mem, False) for mem in aut.get_memories()] #initially no goals are satisfied
			#define the initial state
			init_state = Node(None, sensor_props, react_props, act_props, goal_props, curr_region.get_name())
			#search for the initial state in this automaton
			#and append it to the list of current states
			curr_states.append(aut.get_equal_node(init_state))

		#Let's run each automaton
		done = False
		done_on_next_iter = False
		while not done:
			if done_on_next_iter:
				done = True
			#we sense the current region
			curr_pos, curr_orient = self.robot.get_pose()
			curr_region = self.map.get_region_from_point(curr_pos)
			curr_objects = curr_region.get_objects()
			curr_sensors = [(obj.get_type(), True) for obj in curr_objects]
			
			#DEBUG
			#print "Current sensors: ", curr_sensors

			actuators = []
			successors = []
			successor = None
			#Get the current state in each automaton and
			#go through its successors to find the actions to do
			for i, curr_state in enumerate(curr_states):

				#DEBUG
				#print "CURRENT STATE {}:".format(i)
				#curr_state.pprint()
				#print

				for succ in curr_state.get_successors():
					#get only the true sensor propositions of this successor
					succ_sensors = [(prop, truth) for prop, truth in succ.get_sensors() if truth]
				
					#DEBUG
					#print "Candidate Successor: "
					#succ.pprint()
					#print "Successor sensors: ", succ_sensors
					#print
				
					#if ALL successor sensors match current sensors
					#we found the right successor
					is_successor = True
					if succ_sensors == [] and curr_sensors != []:
						is_successor = False
					for succ_sensor in succ_sensors:
						if not succ_sensor in curr_sensors:
							is_successor = False
							break
					if is_successor:
						for curr_sensor in curr_sensors:
							if not curr_sensor in succ_sensors:
								is_successor = False
								break
					if is_successor:
						successor = succ
						break

				if not successor:
					raise Exception("ERROR: Unable to find a successor state in automaton {}.".format(str(i)))
				
				successors.append(successor)

			#if any of the successors has actions to 
			#execute, we must execute them
			#otherwise we can't move before taking the actions
			next_actuators = []
			for s in successors:
				for (act, truth) in s.get_actuators():
					if truth:
						if not act in next_actuators:
							next_actuators.append(act)

			#DEBUG
			#print "NEXT ACTUATORS:"
			#print next_actuators
			#print

			#an action may be present in one successor
			#and its negation in another successor,
			#in that case we must not do that action
			done_actuators = []
			for a in next_actuators:
				#If it's a negated action we skip it
				if "not_" in a:
					continue
				#if the negation of action a is present 
				#in another successor we must skip this
				#action as well 
				elif "not_{}".format(a) in next_actuators:
					continue
				else:
					if not a in done_actuators:
						self.robot.do_action(a, curr_region, curr_objects, self.widget, self.bomb_objects, self.hostage_objects)
						done_actuators.append(a)

			#after all actions have been executed
			#we can eliminate the objects from this region
			#as they are not useful anymore (in this way
			#the robot will not sense them in next iterations)
			curr_region.set_objects(obj_list = [])

			#DEBUG
			#print "SUCCESSORS: "
			#for s in successors:
				#s.pprint()
				#print

			#if this was the last iteration we are done:
			if done_on_next_iter:
				return

			#if there were no actions to take, we can move
			if not next_actuators:
				#check that all successors agree on the same
				#region where to go
				next_regions = []
				for s in successors:
					if not s.get_region() in next_regions:
						next_regions.append(s.get_region())

				#DEBUG
				#print "NEXT REGIONS:"
				#print next_regions

				if len(next_regions) != 1:
					raise Exception("ERROR: Can't move to next region. Automatons are inconsistent on the next region where to go.")

				next_region_name = next_regions[0]
				if next_region_name != curr_region.get_name():
					#move to the next region
					goal_region = self.map.get_region(next_region_name)
					goal_point = goal_region.get_random_point()
					self.robot.go_to(goal_point)
					new_pos, new_orient = self.robot.get_pose()

					#DEBUG
					#print "ROBOT POSITION: ", pos
					#print "GOAL REGION: ", goal_region.get_name()
					#print "CURR REGION AFTER MOVE: ", self.map.get_region_from_point(pos).get_name()

					#check if we have correctly moved
					if self.map.get_region_from_point(new_pos).get_name() != goal_region.get_name():
						raise Exception("ERROR: Robot was unable to reach the goal region.")
					else:
						#robot successfuly moved to the goal region
						curr_region = goal_region
			
				#update current states in each automaton
				curr_states = []
				for s in successors:
					curr_states.append(s)

				#finally, we check if there are still goals to pursue
				still_goals = False
				for c in curr_states:
					for (mem, truth) in c.get_memories():
						if not truth:
							still_goals = True

				if not still_goals:
					#we only do one more iteration
					#to execute any remaining actuator
					done_on_next_iter = True

					#DEBUG
					#print "DONE ON NEXT ITERATION..."
			

if __name__ == "__main__":
	num_bombs = 3
	num_hostages = 2
	sim = Simulator({'r1': {'xmin': -3.3 , 'xmax': 3.45, 'ymin': -2.0, 'ymax': 2.45},
					 'r2': {'xmin': -3.0, 'xmax': -0.33, 'ymin': 5.0 , 'ymax': 11.0},
					 'r3': {'xmin': 2.0, 'xmax': 9.0, 'ymin': 5.0, 'ymax': 11.0},
					 'r4': {'xmin': 5.7, 'xmax': 9.0, 'ymin': 0.9, 'ymax': 2.6}},
					 [('r1', 'r2'),('r2', 'r3'), ('r3', 'r4'), ('r1', 'r4')],
					 num_bombs,
					 num_hostages,
					 bomb_sdf_filepath = os.path.abspath("../models/Dynamite/model.sdf"),
					 hostage_sdf_filepath = os.path.abspath("../models/Patrick/model.sdf"))
	

	spec_filepath = os.path.abspath("../LTLMoP/src/examples/searchrescue/rescue.spec")

	#EXAMPLES OF SPECIFICATION
	#sim.run(spec_filepath, "Start in r1\nGo to r3\nIf you see a bomb, defuse it\nIf you see a hostage, interact with him\nIf you see a hostage and a bomb, don't defuse the bomb")
	#sim.run(spec_filepath,
	#		"Start in r1\nGo to r3\nAvoid r4\nIf you see a bomb, defuse it\nIf you see a hostage, interact with him\nIf you see a hostage and a bomb, don't defuse the bomb")
	sim.run(spec_filepath, "Start in r3\nGo to r2")
