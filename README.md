# HRI-Reasoning-Robots
Course Project at Sapienza University of Rome (second semester 2018)

## Dependencies
The code is written in Python 2 and has been tested on Ubuntu 16.04. 
In order to be run, it requires the following dependencies:

• Python 2.7 (NOTE: code does not work with Python 3)

• Java Runtime Environment (need 1.6 or 1.7) and Java Development Kit:
      
      `sudo apt-get install default-jre default-jdk`

• Python NumPy, Scipy, and wxPython:
    
    `sudo apt-get install python-numpy python-scipy python-wxtools`

• Python Polygon2, provided inside the project folder or you can just:
    
    `pip install Polygon2`

• ROS Kinetic (code might not work if you use other ROS versions)

• Gazebo 7 (NOTE: code was tested only on Gazebo 7.14.0)

## Downloading and running the code. 
Before running the code, make sure you have Python on your PATH and 
the command "python" should point to your Python 2 version (not Python 3, 
in case you have both installed). Follow these steps to run the code:

1. Clone this repository to your local machine

2. Go to your ROS installation, and open the turtlebot navigation parameters
file (e.g. using gedit):
    
    `cd /opt/ros/kinetic/share/turtlebot_navigation/param/`
    
    `gedit dwa_local_planner_params.yaml`
On this file set `max_rot_vel` equal to 1.0 (default is 5.0 but this causes
issues in the turtlebot navigation)

3. Open a terminal and go to the project folder:
    
    `cd your/path/to/hri_project`

4. Within the project folder, make the script run.sh executable and then
execute it:
   
   `chmod +x run.sh`
   
   `./run.sh`

5. At this point, Gazebo should start along with several terminal
windows that will pop up on your screen. Look for the window that 
asks to write your specification:

![Alt text](figures/terminal_specification.png?raw=true "Title")

6. Type your commands on the window, pressing ENTER after each command
to add it to the specification (press q and ENTER instead if you 
want to exit). When you are done typing commands, press CTRL+D to send 
the specification to the robot. Now watch the robot execute your
specification in Gazebo.

## Simulation videos
Part 1

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/pZ2h2DDL5E4/0.jpg)](https://www.youtube.com/watch?v=pZ2h2DDL5E4&feature=youtu.be)

Part 2

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/O3EtuK8yWLY/0.jpg)](https://www.youtube.com/watch?v=O3EtuK8yWLY&feature=youtu.be)
