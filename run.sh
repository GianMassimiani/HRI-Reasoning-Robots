#!/bin/bash
xterm -e roslaunch turtlebot_gazebo turtlebot_world.launch world_file:=$PWD/maps/Robot_House_small2 &
sleep 13s
xterm -e roslaunch turtlebot_navigation amcl_demo.launch map_file:=$PWD/maps/House_small2/map2.yaml &
sleep 5s
xterm -e roslaunch turtlebot_rviz_launchers view_navigation.launch --screen &
sleep 3s
xterm -e python $PWD/LTLMoP/src/etc/SLURP/pipelinehost.py &
cd $PWD/src/
xterm -e python main.py