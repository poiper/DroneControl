#!/usr/bin/env python3
"""
Visualize target and actual trajectories inside Gazebo Classic.
"""

import math
import time

import rclpy
from gazebo_msgs.srv import SpawnEntity
from geometry_msgs.msg import Pose, PoseStamped
from rclpy.node import Node


class GazeboTrajectoryVisualizer(Node):
    """Spawn small colored spheres in Gazebo for commanded and actual paths."""

    def __init__(self):
        super().__init__('gazebo_trajectory_visualizer')

        self.declare_parameter('namespace', '/drone_0')
        self.declare_parameter('target_enabled', True)
        self.declare_parameter('actual_enabled', True)
        self.declare_parameter('target_color', '0.1 0.35 1.0 1.0')
        self.declare_parameter('actual_color', '1.0 0.15 0.05 1.0')
        self.declare_parameter('marker_radius', 0.055)
        self.declare_parameter('min_distance', 0.25)
        self.declare_parameter('min_interval', 0.35)
        self.declare_parameter('max_points', 500)
        self.declare_parameter('z_offset', 0.02)

        self.namespace = self.get_parameter('namespace').value
        self.target_enabled = bool(self.get_parameter('target_enabled').value)
        self.actual_enabled = bool(self.get_parameter('actual_enabled').value)
        self.marker_radius = float(self.get_parameter('marker_radius').value)
        self.min_distance = float(self.get_parameter('min_distance').value)
        self.min_interval = float(self.get_parameter('min_interval').value)
        self.max_points = int(self.get_parameter('max_points').value)
        self.z_offset = float(self.get_parameter('z_offset').value)
        self.target_color = self.get_parameter('target_color').value
        self.actual_color = self.get_parameter('actual_color').value

        self.spawn_client = self.create_client(SpawnEntity, '/spawn_entity')
        self.pending = []
        self.counts = {'target': 0, 'actual': 0}
        self.last_position = {'target': None, 'actual': None}
        self.last_time = {'target': 0.0, 'actual': 0.0}
        self.run_id = int(time.time())

        if self.target_enabled:
            self.create_subscription(
                PoseStamped,
                f'{self.namespace}/cmd_pose',
                lambda msg: self.pose_callback('target', msg.pose),
                10,
            )
        if self.actual_enabled:
            self.create_subscription(
                PoseStamped,
                f'{self.namespace}/pose',
                lambda msg: self.pose_callback('actual', msg.pose),
                10,
            )

        self.create_timer(0.05, self.process_queue)
        self.get_logger().info(
            f'Gazebo trajectory visualizer initialized for namespace={self.namespace}'
        )

    def pose_callback(self, kind, pose):
        if self.counts[kind] >= self.max_points:
            return
        now = time.monotonic()
        point = (pose.position.x, pose.position.y, pose.position.z)
        if now - self.last_time[kind] < self.min_interval:
            return
        last = self.last_position[kind]
        if last is not None and self.distance(last, point) < self.min_distance:
            return

        self.last_position[kind] = point
        self.last_time[kind] = now
        self.counts[kind] += 1
        name = f'{kind}_trajectory_{self.run_id}_{self.counts[kind]:04d}'
        color = self.target_color if kind == 'target' else self.actual_color
        self.pending.append((name, point, color))

    @staticmethod
    def distance(a, b):
        return math.sqrt(
            (a[0] - b[0]) ** 2
            + (a[1] - b[1]) ** 2
            + (a[2] - b[2]) ** 2
        )

    def process_queue(self):
        if not self.pending:
            return
        if not self.spawn_client.service_is_ready():
            self.spawn_client.wait_for_service(timeout_sec=0.0)
            return

        name, point, color = self.pending.pop(0)
        request = SpawnEntity.Request()
        request.name = name
        request.xml = self.marker_sdf(name, color)
        request.robot_namespace = ''
        request.reference_frame = 'world'
        request.initial_pose = Pose()
        request.initial_pose.position.x = float(point[0])
        request.initial_pose.position.y = float(point[1])
        request.initial_pose.position.z = float(point[2] + self.z_offset)
        request.initial_pose.orientation.w = 1.0
        self.spawn_client.call_async(request)

    def marker_sdf(self, name, color):
        radius = self.marker_radius
        return f"""<?xml version='1.0'?>
<sdf version='1.6'>
  <model name='{name}'>
    <static>true</static>
    <link name='link'>
      <visual name='visual'>
        <geometry>
          <sphere>
            <radius>{radius}</radius>
          </sphere>
        </geometry>
        <material>
          <ambient>{color}</ambient>
          <diffuse>{color}</diffuse>
          <specular>0.05 0.05 0.05 1.0</specular>
        </material>
      </visual>
    </link>
  </model>
</sdf>
"""


def main(args=None):
    rclpy.init(args=args)
    node = GazeboTrajectoryVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
