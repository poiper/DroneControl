#!/usr/bin/env python3
"""
无人机状态监控节点
发布无人机的实时状态信息
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from px4_msgs.msg import VehicleStatus, VehicleLocalPosition, SensorCombined
from geometry_msgs.msg import PoseStamped, TwistStamped, AccelStamped
from sensor_msgs.msg import Imu, MagneticField, FluidPressure
from nav_msgs.msg import Odometry
import numpy as np


class DroneStateMonitor(Node):
    """无人机状态监控"""

    def __init__(self):
        super().__init__('drone_state_monitor')
        
        # 声明参数
        self.declare_parameter('vehicle_id', 0)
        self.declare_parameter('update_rate', 50)  # Hz
        self.declare_parameter('namespace', '/drone_0')
        
        self.vehicle_id = self.get_parameter('vehicle_id').value
        self.update_rate = self.get_parameter('update_rate').value
        self.namespace = self.get_parameter('namespace').value
        
        # QoS配置
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        # 订阅PX4消息
        self.vehicle_status_sub = self.create_subscription(
            VehicleStatus,
            f'{self.namespace}/fmu/out/vehicle_status',
            self.vehicle_status_callback,
            qos_profile
        )
        
        self.local_position_sub = self.create_subscription(
            VehicleLocalPosition,
            f'{self.namespace}/fmu/out/vehicle_local_position',
            self.local_position_callback,
            qos_profile
        )
        
        self.sensor_combined_sub = self.create_subscription(
            SensorCombined,
            f'{self.namespace}/fmu/out/sensor_combined',
            self.sensor_combined_callback,
            qos_profile
        )
        
        # 发布ROS标准消息
        self.pose_pub = self.create_publisher(
            PoseStamped,
            f'{self.namespace}/pose',
            10
        )
        
        self.twist_pub = self.create_publisher(
            TwistStamped,
            f'{self.namespace}/twist',
            10
        )
        
        self.accel_pub = self.create_publisher(
            AccelStamped,
            f'{self.namespace}/accel',
            10
        )
        
        self.imu_pub = self.create_publisher(
            Imu,
            f'{self.namespace}/imu',
            10
        )
        
        self.odom_pub = self.create_publisher(
            Odometry,
            f'{self.namespace}/odom',
            10
        )
        
        # 状态变量
        self.position = np.array([0.0, 0.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.acceleration = np.array([0.0, 0.0, 0.0])
        self.att_q = np.array([0.0, 0.0, 0.0, 1.0])  # 四元数 [x, y, z, w]
        
        self.is_armed = False
        self.nav_state = 0
        self.arming_state = 0
        
        # 定时发布
        timer_period = 1.0 / self.update_rate
        self.timer = self.create_timer(timer_period, self.publish_state)
        
        self.get_logger().info(
            f'Drone State Monitor initialized (vehicle_id={self.vehicle_id}, '
            f'update_rate={self.update_rate}Hz)'
        )

    def vehicle_status_callback(self, msg: VehicleStatus):
        """处理无人机状态"""
        self.is_armed = bool(msg.arming_state == VehicleStatus.ARMING_STATE_ARMED)
        self.nav_state = msg.nav_state
        self.arming_state = msg.arming_state
        
        # 状态日志
        nav_state_names = {
            0: 'MANUAL',
            1: 'ALTCTL',
            2: 'POSCTL',
            3: 'AUTO_MISSION',
            4: 'AUTO_LOITER',
            5: 'AUTO_RTH',
            6: 'ACRO',
            7: 'OFFBOARD',
            8: 'STABILIZED',
            9: 'RATTITUDE',
            10: 'AUTO_TAKEOFF',
            11: 'AUTO_LAND',
            12: 'AUTO_FOLLOW_TARGET',
            13: 'AUTO_PRECISION_LAND',
            14: 'ORBIT',
            15: 'AUTO_VTOL_TAKEOFF',
        }
        
        nav_state_str = nav_state_names.get(self.nav_state, f'UNKNOWN({self.nav_state})')

    def local_position_callback(self, msg: VehicleLocalPosition):
        """处理本地位置"""
        self.position = np.array([msg.x, msg.y, msg.z])
        self.velocity = np.array([msg.vx, msg.vy, msg.vz])

    def sensor_combined_callback(self, msg: SensorCombined):
        """处理传感器数据"""
        # 加速度
        self.acceleration = np.array([
            msg.accelerometer_m_s2[0],
            msg.accelerometer_m_s2[1],
            msg.accelerometer_m_s2[2]
        ])

    def publish_state(self):
        """发布无人机状态"""
        timestamp = self.get_clock().now()
        
        # 发布PoseStamped
        pose_msg = PoseStamped()
        pose_msg.header.stamp = timestamp.to_msg()
        pose_msg.header.frame_id = f'drone_{self.vehicle_id}'
        pose_msg.pose.position.x = self.position[0]
        pose_msg.pose.position.y = self.position[1]
        pose_msg.pose.position.z = self.position[2]
        pose_msg.pose.orientation.x = self.att_q[0]
        pose_msg.pose.orientation.y = self.att_q[1]
        pose_msg.pose.orientation.z = self.att_q[2]
        pose_msg.pose.orientation.w = self.att_q[3]
        
        self.pose_pub.publish(pose_msg)
        
        # 发布TwistStamped
        twist_msg = TwistStamped()
        twist_msg.header.stamp = timestamp.to_msg()
        twist_msg.header.frame_id = f'drone_{self.vehicle_id}'
        twist_msg.twist.linear.x = self.velocity[0]
        twist_msg.twist.linear.y = self.velocity[1]
        twist_msg.twist.linear.z = self.velocity[2]
        
        self.twist_pub.publish(twist_msg)
        
        # 发布AccelStamped
        accel_msg = AccelStamped()
        accel_msg.header.stamp = timestamp.to_msg()
        accel_msg.header.frame_id = f'drone_{self.vehicle_id}'
        accel_msg.accel.linear.x = self.acceleration[0]
        accel_msg.accel.linear.y = self.acceleration[1]
        accel_msg.accel.linear.z = self.acceleration[2]
        
        self.accel_pub.publish(accel_msg)
        
        # 发布Odometry
        odom_msg = Odometry()
        odom_msg.header.stamp = timestamp.to_msg()
        odom_msg.header.frame_id = 'world'
        odom_msg.child_frame_id = f'drone_{self.vehicle_id}'
        odom_msg.pose.pose.position.x = self.position[0]
        odom_msg.pose.pose.position.y = self.position[1]
        odom_msg.pose.pose.position.z = self.position[2]
        odom_msg.pose.pose.orientation.x = self.att_q[0]
        odom_msg.pose.pose.orientation.y = self.att_q[1]
        odom_msg.pose.pose.orientation.z = self.att_q[2]
        odom_msg.pose.pose.orientation.w = self.att_q[3]
        odom_msg.twist.twist.linear.x = self.velocity[0]
        odom_msg.twist.twist.linear.y = self.velocity[1]
        odom_msg.twist.twist.linear.z = self.velocity[2]
        
        self.odom_pub.publish(odom_msg)


def main(args=None):
    rclpy.init(args=args)
    monitor = DroneStateMonitor()
    
    try:
        rclpy.spin(monitor)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
