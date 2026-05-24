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
    
    # 获取world文件路径
    world_path = os.path.join(drone_control_dir, 'worlds', 'empty_world.world')
    
    # 检查world文件是否存在，如果不存在使用默认的empty world
    if not os.path.exists(world_path):
        world_path = 'worlds/empty.world'
    
    start_gazebo = LaunchConfiguration('start_gazebo')
    start_px4 = LaunchConfiguration('start_px4')
    px4_dir = LaunchConfiguration('px4_dir')
    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    
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
        }]
    )
    ld.add_action(offboard_controller)
    
    return ld
