#!/usr/bin/env python3
"""
Publish repeatable offboard trajectories and record tracking error.
"""

import csv
import math
import os
from datetime import datetime

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node


class TrajectoryExperiment(Node):
    """Command a simple trajectory and log actual-vs-target position."""

    def __init__(self):
        super().__init__('trajectory_experiment')

        self.declare_parameter('namespace', '/drone_0')
        self.declare_parameter('pattern', 'circle')
        self.declare_parameter('altitude', 2.0)
        self.declare_parameter('radius', 2.0)
        self.declare_parameter('speed', 0.6)
        self.declare_parameter('duration', 60.0)
        self.declare_parameter('publish_rate', 20.0)
        self.declare_parameter('output_file', '')

        self.namespace = self.get_parameter('namespace').value
        self.pattern = self.get_parameter('pattern').value
        self.altitude = float(self.get_parameter('altitude').value)
        self.radius = float(self.get_parameter('radius').value)
        self.speed = float(self.get_parameter('speed').value)
        self.duration = float(self.get_parameter('duration').value)
        self.publish_rate = float(self.get_parameter('publish_rate').value)
        output_file = self.get_parameter('output_file').value

        if not output_file:
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'/tmp/drone_trajectory_{self.pattern}_{stamp}.csv'
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

        self.cmd_pub = self.create_publisher(PoseStamped, f'{self.namespace}/cmd_pose', 10)
        self.pose_sub = self.create_subscription(
            PoseStamped,
            f'{self.namespace}/pose',
            self.pose_callback,
            10,
        )

        self.start_time = self.get_clock().now()
        self.latest_pose = None
        self.finished = False
        self.csv_file = open(output_file, 'w', newline='', encoding='utf-8')
        self.csv = csv.writer(self.csv_file)
        self.csv.writerow([
            'time_s',
            'target_x',
            'target_y',
            'target_z',
            'actual_x',
            'actual_y',
            'actual_z',
            'error_m',
        ])

        period = 1.0 / max(self.publish_rate, 1.0)
        self.timer = self.create_timer(period, self.timer_callback)
        self.get_logger().info(
            f'Running {self.pattern} trajectory for {self.duration:.1f}s, '
            f'logging to {output_file}'
        )

    def pose_callback(self, msg):
        self.latest_pose = msg

    def target_at(self, time_s):
        altitude = abs(self.altitude)
        if self.pattern == 'hover':
            return 0.0, 0.0, altitude
        if self.pattern == 'line':
            period = max(4.0 * self.radius / max(self.speed, 0.1), 1.0)
            phase = (time_s % period) / period
            x = -self.radius + 4.0 * self.radius * phase
            if x > self.radius:
                x = 3.0 * self.radius - x
            return x, 0.0, altitude
        if self.pattern == 'figure8':
            omega = self.speed / max(self.radius, 0.1)
            angle = omega * time_s
            return (
                self.radius * math.sin(angle),
                self.radius * math.sin(angle) * math.cos(angle),
                altitude,
            )

        omega = self.speed / max(self.radius, 0.1)
        angle = omega * time_s
        return (
            self.radius * math.cos(angle),
            self.radius * math.sin(angle),
            altitude,
        )

    def timer_callback(self):
        now = self.get_clock().now()
        elapsed = (now - self.start_time).nanoseconds / 1e9

        if elapsed > self.duration:
            if not self.finished:
                self.finished = True
                self.csv_file.flush()
                self.get_logger().info('Trajectory complete; CSV log flushed')
                rclpy.shutdown()
            return

        target_x, target_y, target_z = self.target_at(elapsed)
        msg = PoseStamped()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = 'world'
        msg.pose.position.x = target_x
        msg.pose.position.y = target_y
        msg.pose.position.z = target_z
        msg.pose.orientation.w = 1.0
        self.cmd_pub.publish(msg)

        if self.latest_pose is None:
            return

        actual = self.latest_pose.pose.position
        error = math.sqrt(
            (actual.x - target_x) ** 2
            + (actual.y - target_y) ** 2
            + (actual.z - target_z) ** 2
        )
        self.csv.writerow([
            f'{elapsed:.3f}',
            f'{target_x:.4f}',
            f'{target_y:.4f}',
            f'{target_z:.4f}',
            f'{actual.x:.4f}',
            f'{actual.y:.4f}',
            f'{actual.z:.4f}',
            f'{error:.4f}',
        ])

    def destroy_node(self):
        self.csv_file.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryExperiment()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
