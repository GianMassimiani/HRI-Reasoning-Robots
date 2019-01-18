#!/usr/bin/env python
from copy import deepcopy
import rospy
import numpy as np
import os

from math import sin, cos


from geometry_msgs.msg import Point, Quaternion, Pose, PoseWithCovariance, PoseWithCovarianceStamped
from gazebo_msgs.srv import GetModelState, SetModelState, SpawnModel, DeleteModel, GetWorldProperties, GetModelProperties
from gazebo_msgs.msg import ModelState
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
import actionlib
from actionlib_msgs.msg import *
import pdb as pdb
from tf.transformations import quaternion_from_euler

class GazeboModel(object):
    def __init__(self, name, relative_entity_name = None, sdf_filepath = None):
        self.name = name
        self.relative_entity_name = relative_entity_name
        self.sdf_filepath = sdf_filepath

    def set_relative_entity_name(self, entity_name):
        self.relative_entity_name = entity_name 

    def set_sdf_filepath(self, filepath):
        self.sdf_filepath = filepath

class GazeboWorld(object):
    """This class is an API to manage 
    the simulated world in gazebo. 
    Common tasks that can be done with the 
    class include for example moving and/or
    deleting 3D models in gazebo.
    """
    def __init__(self):
        self.amcl_subscriber = rospy.Subscriber('/amcl_pose', PoseWithCovarianceStamped, self.callback)
        self.amcl_publisher = rospy.Publisher('initialpose',
                                              PoseWithCovarianceStamped,
                                              queue_size=10)
        rospy.init_node('simulator', anonymous = True)

        self.rate = rospy.Rate(1) # 10hz

        self.move_base_client = actionlib.SimpleActionClient("move_base", MoveBaseAction)
        rospy.loginfo("Wait for the action server to come up")
        # Wait for the action server to come up
        self.move_base_client.wait_for_server()

        #Creating a message with type PoseWithCovarianceStamped
        #this will be used to set the amcl pose of the robot
        self.set_pose = PoseWithCovarianceStamped()
        self.set_pose.header.frame_id = "map"

        #This will be used to send a navigation goal
        #to the robot
        self.goal = MoveBaseGoal()
        self.goal.target_pose.header.frame_id = 'map'

    def callback(self, msg):
        self.amcl_pose = msg

    def get_robot_amcl_pose(self):
        """Return the current robot pose in the Rviz map."""
        if not self.amcl_pose:
            raise Exception("Can't get amcl pose. Make sure amcl was launched correctly, e.g. 'roslaunch turtlebot_navigation amcl_demo.launch map_file:=/path/to/yaml/file'")
        return self.amcl_pose

    def set_robot_amcl_pose(self, target_point, target_orientation):
        """Traslate the robot to the given pose in the Rviz map."""
        coordinates = Point(target_point[0], target_point[1], 0)

        for angle in target_orientation:
            if angle > np.pi or angle < -np.pi:
                raise Exception("Angles must be >=0 and <=pi [rad] (angles between 0 and 180 degrees) or =<0 and >=-pi [rad] (angles between 180 and 360 degrees)")

        numpy_quaternion = quaternion_from_euler(0, 0, target_orientation[2])
        orientation = Quaternion(numpy_quaternion[0],
                                 numpy_quaternion[1],
                                 numpy_quaternion[2],
                                 numpy_quaternion[3])

        target_pose = PoseWithCovariance()
        target_pose.pose = Pose(coordinates,
                                orientation)

        rospy.loginfo("Setting pose: ")
        rospy.loginfo(target_pose)

        self.set_pose.pose = target_pose
        
        while not np.allclose(np.array([self.amcl_pose.pose.pose.position.x,
                                        self.amcl_pose.pose.pose.position.y,
                                        self.amcl_pose.pose.pose.position.z,
                                        self.amcl_pose.pose.pose.orientation.x,
                                        self.amcl_pose.pose.pose.orientation.y,
                                        self.amcl_pose.pose.pose.orientation.z,
                                        self.amcl_pose.pose.pose.orientation.w]),
                              np.array([self.set_pose.pose.pose.position.x,
                                        self.set_pose.pose.pose.position.y,
                                        self.set_pose.pose.pose.position.z,
                                        self.set_pose.pose.pose.orientation.x,
                                        self.set_pose.pose.pose.orientation.y,
                                        self.set_pose.pose.pose.orientation.z,
                                        self.set_pose.pose.pose.orientation.w]),
                               rtol=1e-01, atol=1e-02):
            self.amcl_publisher.publish(self.set_pose)
            self.rate.sleep()
        rospy.loginfo("Done setting the pose.")
        """
        #ALTERNATIVE WAY TO PUBLISH THE POSE
        while not (float("{0:.2f}".format(self.amcl_pose.pose.pose.position.x)) == float("{0:.2f}".format(self.set_pose.pose.pose.position.x)) and
                   float("{0:.2f}".format(self.amcl_pose.pose.pose.position.y)) == float("{0:.2f}".format(self.set_pose.pose.pose.position.y)) and
                   float("{0:.2f}".format(self.amcl_pose.pose.pose.position.z)) == float("{0:.2f}".format(self.set_pose.pose.pose.position.z)) and
                   float("{0:.2f}".format(self.amcl_pose.pose.pose.orientation.x)) == float("{0:.2f}".format(self.set_pose.pose.pose.orientation.x)) and
                   float("{0:.2f}".format(self.amcl_pose.pose.pose.orientation.y)) == float("{0:.2f}".format(self.set_pose.pose.pose.orientation.y)) and
                   float("{0:.2f}".format(self.amcl_pose.pose.pose.orientation.z)) == float("{0:.2f}".format(self.set_pose.pose.pose.orientation.z)) and
                   float("{0:.2f}".format(self.amcl_pose.pose.pose.orientation.w)) == float("{0:.2f}".format(self.set_pose.pose.pose.orientation.w))):
            self.amcl_publisher.publish(self.set_pose)
            self.rate.sleep()
        """

    def get_model_names(self):
        """Return a list with names of all
        the models currently present
        in the simulation."""
        try:
            get_world_properties = rospy.ServiceProxy('/gazebo/get_world_properties', GetWorldProperties)
            model_names = get_world_properties().model_names
        except rospy.ServiceException as e:
            rospy.loginfo("Get World Properties service call failed:  {0}".format(e))
            return

        return model_names

    def get_model_entities(self, model_name):
        """Return a list with names of all the 
        entities (links, wheels, etc.) of the 
        given model."""
        try:
            get_model_properties = rospy.ServiceProxy('/gazebo/get_model_properties', GetModelProperties)
            for model in self.get_model_names():
                if model == model_name:
                    model_entities = get_model_properties(model).body_names
                    break
        except rospy.ServiceException as e:
            rospy.loginfo("Get Model Properties service call failed:  {0}".format(e))
            return

        return model_entities

    def get_model_state(self, model):
        """Return the current pose of the 
        given model in the world."""
        if not isinstance(model, GazeboModel):
            raise Exception("Model must be an instance of GazeboModel.")

        try:
            get_state = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState)
            #Get state of single model
            model_state = get_state(model.name, model.relative_entity_name)
            if not model_state.success:
                rospy.loginfo("Could not retrieve state for model '{}'".format(model_name)) 
        except rospy.ServiceException as e:
            rospy.loginfo("Get Model State service call failed:  {0}".format(e))
            return

        return model_state

    def set_model_state(self, model, target_point, target_orientation):
        """Traslate the given model to the given pose
        in the world.
        
        params:
        model:              instance of GazeboModel
        target_point:       [x, y, z]
        target_orientation: [roll, pitch, yaw]
        """
        for angle in target_orientation:
            if angle > np.pi or angle < -np.pi:
                raise Exception("Angles must be >=0 and <=pi [rad] (angles between 0 and 180 degrees) or =<0 and >=-pi [rad] (angles between 180 and 360 degrees)")
        
        if not isinstance(model, GazeboModel):
            raise Exception("Model must be an instance of GazeboModel.")

        numpy_quaternion = quaternion_from_euler(target_orientation[0],
                                                 target_orientation[1],
                                                 target_orientation[2])
        
        target_pose = Pose(Point(target_point[0], target_point[1], target_point[2]),
                          Quaternion(numpy_quaternion[0],
                                     numpy_quaternion[1],
                                     numpy_quaternion[2],
                                     numpy_quaternion[3]))
        try:
            set_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)

            state = ModelState()
            state.model_name = model.name
            state.pose = target_pose

            rospy.loginfo("Moving model '%s' to (%s, %s) position", model.name, target_pose.position.x, target_pose.position.y)
            result = set_state(state)

            if result.success:
                rospy.loginfo("Model '{}' successfully moved.".format(model.name))
            else:
                rospy.loginfo("ERROR: could not move model '{}'".format(model.name))
        except rospy.ServiceException as e:
            rospy.loginfo("Set Model State service call failed:  {0}".format(e))
            return False

        return result.success

    def spawn_model(self, model, model_point, model_orientation,
                    robot_namespace = "", reference_frame = "world"):
        if not isinstance(model, GazeboModel):
            raise Exception("Model must be an instance of GazeboModel.")
        
        if not model.sdf_filepath:
            raise Exception("ERROR: Can't spawn model. No sdf file specified.")
        for angle in model_orientation:
            if angle > np.pi or angle < -np.pi:
                raise Exception("Angles must be >=0 and <=pi [rad] (angles between 0 and 180 degrees) or =<0 and >=-pi [rad] (angles between 180 and 360 degrees)")
        
        numpy_quaternion = quaternion_from_euler(model_orientation[0],
                                                 model_orientation[1],
                                                 model_orientation[2])
        model_pose = Pose(Point(model_point[0], model_point[1], model_point[2]),
                          Quaternion(numpy_quaternion[0],
                                     numpy_quaternion[1],
                                     numpy_quaternion[2],
                                     numpy_quaternion[3]))

        rospy.loginfo("Waiting for service gazebo/spawn_model")
        rospy.wait_for_service("gazebo/spawn_sdf_model")

        try:
            spawn_sdf_model = rospy.ServiceProxy("gazebo/spawn_sdf_model", SpawnModel)
            with open(model.sdf_filepath, "r") as f:
                model_xml = f.read()
            rospy.loginfo("Spawning model '%s' at position (%s,%s,%s)", model.name,
                                                                        model_point[0],
                                                                        model_point[1],
                                                                        model_point[2])
            result = spawn_sdf_model(model.name, model_xml, robot_namespace, model_pose, reference_frame)
            if result.success:
                rospy.loginfo("Model successfully spawned.")
            else:
                rospy.loginfo("Error: could not spawn model '{}".format(model.name))
        except rospy.ServiceException as e:
            rospy.loginfo("Spawn Model service call failed:  {0}".format(e))
            return False

        return result.success


    def delete_model(self, model):
        """Remove model from the Gazebo world."""
        if not isinstance(model, GazeboModel):
            raise Exception("Model must be an instance of GazeboModel.")
        try:
            rospy.loginfo("Deleting model '{}'".format(model.name))

            del_model = rospy.ServiceProxy('gazebo/delete_model', DeleteModel)
            del_model(model.name)
            
            rospy.loginfo("Model successfully deleted.")
        except rospy.ServiceException as e:
            rospy.loginfo("Set Model State service call failed:  {0}".format(e))
            return

    def navigate_to_goal(self, goal_point, goal_orientation):
        """Navigate the robot to given pose in the Rviz map.

        params:
        goal_point:       [x, y, z]
        goal_orientation: [roll, pitch, yaw]
        """
        for angle in goal_orientation:
            if angle > np.pi or angle < -np.pi:
                raise Exception("Angles must be >=0 and <=pi [rad] (angles between 0 and 180 degrees) or =<0 and >=-pi [rad] (angles between 180 and 360 degrees)")

        numpy_quaternion = quaternion_from_euler(goal_orientation[0],
                                                 goal_orientation[1],
                                                 goal_orientation[2])

        goal_pose = Pose(Point(goal_point[0],
                               goal_point[1],
                               goal_point[2]),
                         Quaternion(numpy_quaternion[0],
                                    numpy_quaternion[1],
                                    numpy_quaternion[2],
                                    numpy_quaternion[3]))

        try:
            self.goal.target_pose.header.stamp = rospy.Time.now()
            self.goal.target_pose.pose = goal_pose

            # Start moving
            rospy.loginfo("Navigating to (%s, %s) position", goal_pose.position.x, goal_pose.position.y)
            self.move_base_client.send_goal(self.goal)
            # Allow TurtleBot up to 60 seconds to complete task
            success = self.move_base_client.wait_for_result(rospy.Duration(60)) 

            state = self.move_base_client.get_state()
            result = False

            if success and state == GoalStatus.SUCCEEDED:
                # We made it!
                result = True
                rospy.loginfo("Turtlebot reached the desired pose")
            else:
                self.move_base_client.cancel_goal()
                rospy.loginfo("Turtlebot failed to reach the desired pose")

            return result
        except rospy.ServiceException as e:
            rospy.loginfo("Service call failed:  {0}".format(e))
            return



class amclPoseGetter(object):
    """This class only reads the pose of the robot in Rviz."""
    def __init__(self):
        # Create a node
        rospy.init_node("amcl_pose_getter")
        # Make sure sim time is working
        while not rospy.Time.now():
            pass
        self.amcl_subscriber = rospy.Subscriber('/amcl_pose', PoseWithCovarianceStamped, self.callback)
        self.amcl_pose = None
        
        while not rospy.is_shutdown():
            pass

    def callback(self, msg):
        self.amcl_pose = msg
        #print "I've read amcl pose at time: ", rospy.Time.now()
        #print "Pose: ", repr(self.amcl_pose)

    def get_pose(self):
        return self.amcl_pose

if __name__ == "__main__":
    world = GazeboWorld()

    #-----TEST get amcl pose---
    pose = world.get_robot_amcl_pose()
    print "Robot amcl pose: ", pose
    print type(pose)

    #-----TEST set amcl pose---
    #world.set_robot_amcl_pose([2.6789, 0.33214, 0.0], [0.0, 0.0, -2.64159])

    #-----TEST get model names---
    #print "Models: ", world.get_model_names()

    #-----TEST get model entities---
    """
    models = world.get_model_names()
    for model_name in models:
        print model_name, ": ", world.get_model_entities(model_name)
        if model_name == "Robot_house_small2":
            entities = world.get_model_entities(model_name)
            for ent in entities:
                print ent
                model = GazeboModel(model_name, ent)
                print world.get_model_state(model)
    """

    #-----TEST get model state---
    """
    print "Model states:"
    for model_name in world.get_model_names():
        entities = world.get_model_entities(model_name)
        model = GazeboModel(model_name, entities[0])
        state = world.get_model_state(model)
        print model_name + ": "
        print type(state.pose.position)
        print type(state.pose.orientation)
        print type(state)
        print
    """
    
    #-----TEST set model state---
    """
    models = world.get_model_names()
    robot_name = models[1]
    entities = world.get_model_entities(robot_name)
    model = GazeboModel(robot_name, entities[0])

    numpy_quaternion = quaternion_from_euler(0.0, 0.0, 1.58)
    target_state = Pose(Point(4.3, 2.4, 0.0),
                        Quaternion(numpy_quaternion[0],
                                   numpy_quaternion[1],
                                   numpy_quaternion[2],
                                   numpy_quaternion[3]))
    world.set_model_state(model, target_state)
    """

    #----TEST delete model and navigate to goal---
    #We make turtlebot navigate to a goal point,
    #after that we remove a test model in the world
    #Note: this test works only if there is a test sphere in the world
    """
    models = world.get_model_names()
    for model_name in models:
        if model_name == 'unit_sphere':
            entities = world.get_model_entities(model_name)
            sphere = GazeboModel(model_name, entities[0])
    world.navigate_to_goal([6.0, 0.6, 0.0], [0.0, 0.0, 0.0])
    world.delete_model(sphere)
    """

    #-----TEST spawn model---
    """
    model_name = "Dynamite2"
    model_sdf_filepath = os.path.abspath("../models/Dynamite/model.sdf")
    model = GazeboModel(model_name, sdf_filepath = model_sdf_filepath)
    result = world.spawn_model(model,
                         [0.5, 0.9, 0.0],
                         [0.0, 0.0, 0.0],
                         "",
                         "world")
    """
