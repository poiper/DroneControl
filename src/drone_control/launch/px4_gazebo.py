#!/usr/bin/env python3
"""
ROS2 Launch文件：启动Gazebo仿真和PX4 SITL
用于虚拟无人机仿真环境
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # 获取包目录
    drone_control_dir = get_package_share_directory('drone_control')
    
    default_world_path = os.path.join(drone_control_dir, 'worlds', 'empty_world.world')
    
    start_gazebo = LaunchConfiguration('start_gazebo')
    start_px4 = LaunchConfiguration('start_px4')
    px4_dir = LaunchConfiguration('px4_dir')
    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    world_path = LaunchConfiguration('world')
    auto_takeoff = LaunchConfiguration('auto_takeoff')
    takeoff_altitude = LaunchConfiguration('takeoff_altitude')
    start_experiment = LaunchConfiguration('start_experiment')
    experiment_pattern = LaunchConfiguration('experiment_pattern')
    experiment_duration = LaunchConfiguration('experiment_duration')
    start_trajectory_visualizer = LaunchConfiguration('start_trajectory_visualizer')
    
    ld = LaunchDescription([
        DeclareLaunchArgument(
            'start_gazebo',
            default_value='false',
            description='Start Gazebo from this launch file. Keep false when PX4 make target already starts Gazebo.'
        ),
        DeclareLaunchArgument(
            'start_px4',
            default_value='false',
            description='Start PX4 SITL via make px4_sitl gazebo.'
        ),
        DeclareLaunchArgument(
            'px4_dir',
            default_value=os.path.expanduser('~/development/PX4-Autopilot'),
            description='PX4-Autopilot source directory.'
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock. Keep false unless a ROS /clock topic is available.'
        ),
        DeclareLaunchArgument(
            'namespace',
            default_value='/drone_0',
            description='ROS namespace prefix used by PX4 uXRCE-DDS topics.'
        ),
        DeclareLaunchArgument(
            'world',
            default_value=default_world_path,
            description='Gazebo world file used when start_gazebo is true.'
        ),
        DeclareLaunchArgument(
            'auto_takeoff',
            default_value='true',
            description='Publish a default takeoff/hover setpoint from px4_offboard.'
        ),
        DeclareLaunchArgument(
            'takeoff_altitude',
            default_value='2.0',
            description='Default hover altitude in meters for auto_takeoff.'
        ),
        DeclareLaunchArgument(
            'start_experiment',
            default_value='false',
            description='Start trajectory_experiment to publish a repeatable test path.'
        ),
        DeclareLaunchArgument(
            'experiment_pattern',
            default_value='circle',
            description='Trajectory pattern: hover, line, circle, or figure8.'
        ),
        DeclareLaunchArgument(
            'experiment_duration',
            default_value='60.0',
            description='Trajectory experiment duration in seconds.'
        ),
        DeclareLaunchArgument(
            'start_trajectory_visualizer',
            default_value='false',
            description='Show commanded and actual trajectory points inside Gazebo.'
        ),
    ])
    
    # ========================
    # 1. 可选：启动Gazebo仿真环境
    # ========================
    gazebo_launch = ExecuteProcess(
        cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_init.so', 
             '-s', 'libgazebo_ros_factory.so', world_path],
        output='screen',
        condition=IfCondition(start_gazebo)
    )
    ld.add_action(gazebo_launch)
    
    # ========================
    # 2. 可选：启动PX4 SITL
    # ========================
    px4_sitl = ExecuteProcess(
        cmd=['make', 'px4_sitl', 'gazebo'],
        cwd=px4_dir,
        output='screen',
        condition=IfCondition(start_px4),
        additional_env={
            'PX4_HOME_LAT': '47.397742',
            'PX4_HOME_LON': '8.545594',
            'PX4_HOME_ALT': '488',
        }
    )
    ld.add_action(px4_sitl)
    
    # ========================
    # 3. 启动ROS2节点
    # ========================
    
    # 无人机状态监控节点
    state_monitor = Node(
        package='drone_control',
        executable='drone_state_monitor',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'namespace': namespace,
        }],
    )
    ld.add_action(state_monitor)

    # Gazebo仿真接口节点
    sim_interface = Node(
        package='drone_control',
        executable='gazebo_sim_interface',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'namespace': namespace,
            'vehicle_id': 0,
            'enable_ground_truth': True,
        }]
    )
    ld.add_action(sim_interface)

    # Offboard控制节点
    offboard_controller = Node(
        package='drone_control',
        executable='px4_offboard',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'namespace': namespace,
            'vehicle_id': 0,
            'target_system': 1,
            'arm_timeout': 10.0,
            'auto_takeoff': auto_takeoff,
            'takeoff_altitude': takeoff_altitude,
        }]
    )
    ld.add_action(offboard_controller)

    trajectory_experiment = Node(
        package='drone_control',
        executable='trajectory_experiment',
        output='screen',
        condition=IfCondition(start_experiment),
        parameters=[{
            'use_sim_time': use_sim_time,
            'namespace': namespace,
            'pattern': experiment_pattern,
            'duration': experiment_duration,
            'altitude': takeoff_altitude,
        }]
    )
    ld.add_action(trajectory_experiment)

    trajectory_visualizer = Node(
        package='drone_control',
        executable='gazebo_trajectory_visualizer',
        output='screen',
        condition=IfCondition(start_trajectory_visualizer),
        parameters=[{
            'use_sim_time': use_sim_time,
            'namespace': namespace,
        }]
    )
    ld.add_action(trajectory_visualizer)
    
    return ld
