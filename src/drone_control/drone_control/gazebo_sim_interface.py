#!/usr/bin/env python3
"""
Gazebo仿真接口节点
连接Gazebo仿真和ROS2控制系统
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from geometry_msgs.msg import PoseStamped, TwistStamped
import numpy as np


class GazeboSimInterface(Node):
    """Gazebo仿真接口"""

    def __init__(self):
        super().__init__('gazebo_sim_interface')
        
        # 声明参数
        self.declare_parameter('vehicle_id', 0)
        self.declare_parameter('enable_ground_truth', True)
        self.declare_parameter('namespace', '/drone_0')
        self.declare_parameter('sim_model_name', 'iris')
        
        self.vehicle_id = self.get_parameter('vehicle_id').value
        self.enable_ground_truth = self.get_parameter('enable_ground_truth').value
        self.namespace = self.get_parameter('namespace').value
        self.sim_model_name = self.get_parameter('sim_model_name').value
        
        # 创建客户端
        self.get_logger().info(f'Gazebo Sim Interface initialized (vehicle_id={self.vehicle_id})')
        
        # 发布器
        self.pose_pub = self.create_publisher(
            PoseStamped,
            f'{self.namespace}/ground_truth/pose',
            10
        )
        
        self.twist_pub = self.create_publisher(
            TwistStamped,
            f'{self.namespace}/ground_truth/twist',
            10
        )
        
        # 状态
        self.last_pose = None
        self.last_twist = None
        
        # 定时器
        self.create_timer(0.02, self.timer_callback)  # 50Hz

    def timer_callback(self):
        """定时回调"""
        try:
            # 这里可以添加Gazebo API调用来获取模型状态
            # 目前这是一个框架，实际实现需要gazebo-ros插件的支持
            pass
        except Exception as e:
            self.get_logger().warn(f'Error in timer callback: {e}')

    def get_model_state(self):
        """获取模型状态"""
        # 这需要使用gazebo_ros服务
        pass


def main(args=None):
    rclpy.init(args=args)
    interface = GazeboSimInterface()
    
    try:
        rclpy.spin(interface)
    except KeyboardInterrupt:
        pass
    finally:
        interface.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
