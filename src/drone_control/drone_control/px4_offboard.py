#!/usr/bin/env python3
"""
PX4 Offboard模式控制节点
提供对无人机的ROS2接口控制
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from px4_msgs.msg import OffboardControlMode, TrajectorySetpoint, VehicleCommand
from px4_msgs.msg import VehicleStatus, VehicleLocalPosition
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist, PoseStamped
import numpy as np
from dataclasses import dataclass
import math


@dataclass
class DroneState:
    """无人机状态"""
    position: np.ndarray = None  # [x, y, z]
    velocity: np.ndarray = None  # [vx, vy, vz]
    attitude: np.ndarray = None  # [roll, pitch, yaw]
    is_armed: bool = False
    in_offboard_mode: bool = False


class PX4OffboardController(Node):
    """PX4 Offboard模式控制器"""

    def __init__(self):
        super().__init__('px4_offboard_controller')
        
        # 声明参数
        self.declare_parameter('vehicle_id', 0)
        self.declare_parameter('target_system', 1)
        self.declare_parameter('arm_timeout', 10.0)
        self.declare_parameter('namespace', '/drone_0')
        self.declare_parameter('auto_takeoff', True)
        self.declare_parameter('takeoff_altitude', 2.0)
        self.declare_parameter('setpoint_rate', 50.0)
        
        self.vehicle_id = self.get_parameter('vehicle_id').value
        self.target_system = self.get_parameter('target_system').value
        self.arm_timeout = self.get_parameter('arm_timeout').value
        self.namespace = self.get_parameter('namespace').value
        self.auto_takeoff = self.get_parameter('auto_takeoff').value
        self.takeoff_altitude = self.get_parameter('takeoff_altitude').value
        self.setpoint_rate = self.get_parameter('setpoint_rate').value
        
        # QoS配置
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        # 发布器
        self.offboard_control_mode_pub = self.create_publisher(
            OffboardControlMode,
            f'{self.namespace}/fmu/in/offboard_control_mode',
            qos_profile
        )
        
        self.trajectory_setpoint_pub = self.create_publisher(
            TrajectorySetpoint,
            f'{self.namespace}/fmu/in/trajectory_setpoint',
            qos_profile
        )
        
        self.vehicle_command_pub = self.create_publisher(
            VehicleCommand,
            f'{self.namespace}/fmu/in/vehicle_command',
            qos_profile
        )
        
        # 订阅器
        self.vehicle_status_sub = self.create_subscription(
            VehicleStatus,
            f'{self.namespace}/fmu/out/vehicle_status',
            self.vehicle_status_callback,
            qos_profile
        )
        
        self.vehicle_local_position_sub = self.create_subscription(
            VehicleLocalPosition,
            f'{self.namespace}/fmu/out/vehicle_local_position',
            self.local_position_callback,
            qos_profile
        )
        
        # 控制指令订阅
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            f'{self.namespace}/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        self.cmd_pos_sub = self.create_subscription(
            PoseStamped,
            f'{self.namespace}/cmd_pose',
            self.cmd_pose_callback,
            10
        )
        
        # 无人机状态
        self.drone_state = DroneState()
        self.have_vehicle_status = False
        self.have_local_position = False
        
        # 定时器
        self.offboard_setpoint_counter = 0
        timer_period = 1.0 / max(float(self.setpoint_rate), 2.0)
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        # 目标值
        initial_z = -abs(float(self.takeoff_altitude)) if self.auto_takeoff else 0.0
        self.target_position = np.array([0.0, 0.0, initial_z])
        self.target_velocity = np.array([0.0, 0.0, 0.0])
        self.target_yaw = 0.0
        self.control_mode = 'position'
        
        self.get_logger().info(
            f'PX4 Offboard Controller initialized (vehicle_id={self.vehicle_id}, '
            f'namespace={self.namespace}, auto_takeoff={self.auto_takeoff}, '
            f'takeoff_altitude={self.takeoff_altitude:.1f}m)'
        )

    def vehicle_status_callback(self, msg: VehicleStatus):
        """处理无人机状态"""
        self.have_vehicle_status = True
        self.drone_state.is_armed = bool(msg.arming_state == VehicleStatus.ARMING_STATE_ARMED)
        self.drone_state.in_offboard_mode = bool(msg.nav_state == VehicleStatus.NAVIGATION_STATE_OFFBOARD)

    def local_position_callback(self, msg: VehicleLocalPosition):
        """处理本地位置"""
        self.have_local_position = True
        self.drone_state.position = np.array([msg.x, msg.y, msg.z])
        self.drone_state.velocity = np.array([msg.vx, msg.vy, msg.vz])

    def cmd_vel_callback(self, msg: Twist):
        """处理速度命令"""
        self.target_velocity = np.array([
            msg.linear.x,
            msg.linear.y,
            -msg.linear.z
        ])
        self.control_mode = 'velocity'
        # 如果提供了角速度，转换yaw速率
        if msg.angular.z != 0:
            self.target_yaw += msg.angular.z * 0.01  # 0.01秒的增量

    def cmd_pose_callback(self, msg: PoseStamped):
        """处理位置命令"""
        self.target_position = np.array([
            msg.pose.position.x,
            msg.pose.position.y,
            -msg.pose.position.z
        ])
        self.control_mode = 'position'
        
        # 从四元数提取yaw角
        qx = msg.pose.orientation.x
        qy = msg.pose.orientation.y
        qz = msg.pose.orientation.z
        qw = msg.pose.orientation.w
        
        self.target_yaw = math.atan2(
            2 * (qw * qz + qx * qy),
            1 - 2 * (qy * qy + qz * qz)
        )

    def arm(self):
        """武装无人机"""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1=1.0
        )
        self.get_logger().info('Arm command sent')

    def disarm(self):
        """解除武装"""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1=0.0
        )
        self.get_logger().info('Disarm command sent')

    def set_offboard_mode(self):
        """设置Offboard模式"""
        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1=1.0,
            param2=6.0
        )
        self.get_logger().info('Offboard mode command sent')

    def publish_vehicle_command(self, command, **params):
        """发布PX4 VehicleCommand。"""
        cmd = VehicleCommand()
        cmd.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        cmd.command = command
        cmd.param1 = float(params.get('param1', 0.0))
        cmd.param2 = float(params.get('param2', 0.0))
        cmd.param3 = float(params.get('param3', 0.0))
        cmd.param4 = float(params.get('param4', 0.0))
        cmd.param5 = float(params.get('param5', 0.0))
        cmd.param6 = float(params.get('param6', 0.0))
        cmd.param7 = float(params.get('param7', 0.0))
        cmd.target_system = self.target_system
        cmd.target_component = 1
        cmd.source_system = 1
        cmd.source_component = 1
        cmd.from_external = True
        self.vehicle_command_pub.publish(cmd)

    def timer_callback(self):
        """定时控制循环"""
        # 发布Offboard控制模式
        offboard_mode = OffboardControlMode()
        offboard_mode.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        offboard_mode.position = self.control_mode == 'position'
        offboard_mode.velocity = self.control_mode == 'velocity'
        offboard_mode.acceleration = False
        offboard_mode.attitude = False
        offboard_mode.body_rate = False
        if hasattr(offboard_mode, 'actuator'):
            offboard_mode.actuator = False
        
        self.offboard_control_mode_pub.publish(offboard_mode)
        
        # 发布轨迹设置点
        trajectory = TrajectorySetpoint()
        trajectory.timestamp = offboard_mode.timestamp
        if self.control_mode == 'position':
            trajectory.position = [float(x) for x in self.target_position]
            trajectory.velocity = [float('nan'), float('nan'), float('nan')]
        else:
            trajectory.position = [float('nan'), float('nan'), float('nan')]
            trajectory.velocity = [float(x) for x in self.target_velocity]
        trajectory.acceleration = [float('nan'), float('nan'), float('nan')]
        trajectory.jerk = [float('nan'), float('nan'), float('nan')]
        trajectory.yaw = self.target_yaw
        trajectory.yawspeed = float('nan')
        
        self.trajectory_setpoint_pub.publish(trajectory)
        
        # 计数器用于确保offboard模式激活
        self.offboard_setpoint_counter += 1
        
        # 每100次循环（1秒）检查一次状态
        if self.offboard_setpoint_counter % 100 == 0:
            if not self.have_vehicle_status:
                self.get_logger().warn(
                    f'No PX4 vehicle_status received on '
                    f'{self.namespace}/fmu/out/vehicle_status. Start PX4 SITL/Gazebo '
                    f'or check the namespace before expecting arm/offboard.'
                )
                return

            if not self.drone_state.is_armed:
                self.get_logger().warn('Drone is not armed!')
                self.arm()
            
            if not self.drone_state.in_offboard_mode:
                self.get_logger().warn('Not in offboard mode!')
                self.set_offboard_mode()
            
            # 状态日志
            if self.drone_state.position is not None:
                self.get_logger().info(
                    f'Position: [{self.drone_state.position[0]:.2f}, '
                    f'{self.drone_state.position[1]:.2f}, '
                    f'{self.drone_state.position[2]:.2f}], '
                    f'Mode: {self.control_mode}, '
                    f'Armed: {self.drone_state.is_armed}, '
                    f'Offboard: {self.drone_state.in_offboard_mode}'
                )
            elif not self.have_local_position:
                self.get_logger().warn(
                    f'No PX4 local_position received on '
                    f'{self.namespace}/fmu/out/vehicle_local_position yet.'
                )


def main(args=None):
    rclpy.init(args=args)
    controller = PX4OffboardController()
    
    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        pass
    finally:
        controller.disarm()
        controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
