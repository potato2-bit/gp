#!/usr/bin/env python3
"""
pvbot_control.launch.py - the rack-and-pinion rail drive done right.

robot_state_publisher holds the URDF (so gazebo_ros2_control can read it),
Gazebo loads the tilted panel + rails, the carriage spawns from the
robot_description topic, then joint_state_broadcaster and the effort-limited
velocity controller come up and pvbot_rail_controller.py sweeps it down and up.

  ros2 launch pvbot_control.launch.py            # GUI
  ros2 launch pvbot_control.launch.py gui:=false # headless (test)
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

HERE = os.path.dirname(os.path.abspath(__file__))
URDF = os.path.join(HERE, 'pvbot_railed_control.urdf')
WORLD = os.path.join(HERE, 'panel_world_tilt.sdf')


def generate_launch_description():
    with open(URDF) as f:
        robot_desc = f.read()
    # gazebo_ros2_control re-emits robot_description as a CLI --param; newlines
    # break the rcl parser, so collapse the URDF to a single line first.
    import re
    robot_desc = re.sub(r'<!--.*?-->', '', robot_desc, flags=re.S)   # drop comments
    robot_desc = ' '.join(robot_desc.split())                         # single line
    gui = LaunchConfiguration('gui')

    rsp = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        output='screen', parameters=[{'robot_description': robot_desc,
                                       'use_sim_time': True}])

    gazebo = ExecuteProcess(
        cmd=['gzserver', WORLD, '-s', 'libgazebo_ros_init.so',
             '-s', 'libgazebo_ros_factory.so'], output='screen')
    gzclient = ExecuteProcess(cmd=['gzclient'], output='screen',
                              condition=IfCondition(gui))

    spawn = Node(package='gazebo_ros', executable='spawn_entity.py',
                 arguments=['-entity', 'pvbot', '-topic', 'robot_description',
                            '-x', '0', '-y', '0', '-z', '0'], output='screen')

    jsb = Node(package='controller_manager', executable='spawner',
               arguments=['joint_state_broadcaster',
                          '--controller-manager', '/controller_manager'],
               output='screen')
    rvc = Node(package='controller_manager', executable='spawner',
               arguments=['rail_velocity_controller',
                          '--controller-manager', '/controller_manager'],
               output='screen')
    sweep = ExecuteProcess(
        cmd=['python3', os.path.join(HERE, 'pvbot_rail_controller.py')],
        output='screen')

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        rsp, gazebo,
        TimerAction(period=4.0, actions=[gzclient]),
        TimerAction(period=7.0, actions=[spawn]),
        TimerAction(period=12.0, actions=[jsb]),
        TimerAction(period=14.0, actions=[rvc]),
        TimerAction(period=16.0, actions=[sweep]),
    ])
