# 虚拟无人机系统用户指南

## 目录
1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [详细操作](#详细操作)
4. [常见任务](#常见任务)
5. [故障排查](#故障排查)

## 系统概述

本系统是一个完整的无人机仿真解决方案，集成了：

- **ROS2 Humble**: 机器人操作系统，提供通信和控制框架
- **PX4 Autopilot**: 开源无人机飞控固件
- **Gazebo**: 3D物理仿真环境
- **自定义ROS节点**: 提供高层控制接口

### 系统架构

```
┌─────────────────────────────────────────┐
│      用户应用层 (Python/ROS2)           │
│  ├─ Offboard 控制                       │
│  ├─ 路径规划                            │
│  └─ 传感器处理                          │
└────────────┬────────────────────────────┘
             │ ROS Topics
┌────────────▼────────────────────────────┐
│     PX4 Autopilot (Offboard Mode)      │
│  ├─ 位置/速度控制                       │
│  ├─ 姿态估计                            │
│  └─ 飞行状态管理                        │
└────────────┬────────────────────────────┘
             │ UDP (SITL)
┌────────────▼────────────────────────────┐
│     Gazebo 仿真环境                     │
│  ├─ Iris 四旋翼                         │
│  ├─ 虚拟传感器                          │
│  └─ 物理引擎                            │
└─────────────────────────────────────────┘
```

### 系统功能

| 功能 | 说明 | 状态 |
|------|------|------|
| **位置控制** | 发送目标位置到无人机 | ✓ 完成 |
| **速度控制** | 实时速度指令 | ✓ 完成 |
| **状态监控** | 获取无人机实时状态 | ✓ 完成 |
| **Gazebo仿真** | 完整的物理仿真 | ✓ 完成 |
| **Offboard模式** | 外部计算机控制 | ✓ 完成 |
| **多无人机** | 支持编队控制 | ◐ 部分 |
| **SLAM集成** | 与SLAM系统集成 | ◐ 部分 |

## 快速开始

### 5分钟入门

#### 步骤1: 验证环境

```bash
python3 ~/FlyControl/ros2_fc/test_system.py
```

如果所有检查通过，继续步骤2。

#### 步骤2: 源配置

```bash
cd ~/FlyControl/ros2_fc
source install/setup.bash
```

#### 步骤3: 启动仿真（3个终端）

**终端A - PX4 SITL:**
```bash
cd ~/development/PX4-Autopilot
make px4_sitl gazebo
```

**终端B - ROS2节点:**
```bash
cd ~/FlyControl/ros2_fc
source install/setup.bash
ros2 launch drone_control px4_gazebo.py
```

**终端C - 验证状态:**
```bash
cd ~/FlyControl/ros2_fc
source install/setup.bash
ros2 topic echo /drone_0/pose
```

你应该看到无人机的位置信息不断更新！

## 详细操作

### 操作1: 查看无人机实时数据

#### 方式1：命令行查看

```bash
# 查看位置信息
ros2 topic echo /drone_0/pose

# 查看速度信息
ros2 topic echo /drone_0/twist

# 查看飞行状态
ros2 topic echo /drone_0/fmu/out/vehicle_status

# 查看本地位置
ros2 topic echo /drone_0/fmu/out/vehicle_local_position
```

#### 方式2：使用RViz可视化

```bash
# 启动RViz
ros2 run rviz2 rviz2

# 配置步骤：
# 1. Fixed Frame: world
# 2. Add -> Pose -> /drone_0/pose
# 3. Add -> Odometry -> /drone_0/odom
```

#### 方式3：编写Python脚本

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

class DroneMonitor(Node):
    def __init__(self):
        super().__init__('drone_monitor')
        self.sub = self.create_subscription(
            PoseStamped,
            '/drone_0/pose',
            self.pose_callback,
            10
        )
    
    def pose_callback(self, msg):
        x = msg.pose.position.x
        y = msg.pose.position.y
        z = msg.pose.position.z
        print(f"Position: ({x:.2f}, {y:.2f}, {z:.2f})")

if __name__ == '__main__':
    rclpy.init()
    node = DroneMonitor()
    rclpy.spin(node)
```

### 操作2: 发送位置命令

#### 方式1：单次命令

```bash
ros2 topic pub -1 /drone_0/cmd_pose geometry_msgs/PoseStamped \
  "{header: {frame_id: 'world'}, pose: {position: {x: 1.0, y: 1.0, z: 2.0}, orientation: {w: 1.0}}}"
```

#### 方式2：连续命令（Python）

```python
import rclpy
from geometry_msgs.msg import PoseStamped
from math import sin, cos, pi
import time

rclpy.init()
node = rclpy.create_node('position_commander')
pub = node.create_publisher(PoseStamped, '/drone_0/cmd_pose', 10)

rate = node.create_rate(10)  # 10 Hz

# 发送方形轨迹
waypoints = [
    (0, 0, 2),
    (2, 0, 2),
    (2, 2, 2),
    (0, 2, 2),
    (0, 0, 2),
]

for x, y, z in waypoints:
    msg = PoseStamped()
    msg.header.frame_id = 'world'
    msg.pose.position.x = float(x)
    msg.pose.position.y = float(y)
    msg.pose.position.z = float(z)
    msg.pose.orientation.w = 1.0
    
    # 发送10秒
    for _ in range(100):
        pub.publish(msg)
        rate.sleep()

rclpy.shutdown()
```

### 操作3: 发送速度命令

```bash
# 前进
ros2 topic pub -1 /drone_0/cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.5, y: 0.0, z: 0.0}}"

# 上升
ros2 topic pub -1 /drone_0/cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.5}}"

# 旋转
ros2 topic pub -1 /drone_0/cmd_vel geometry_msgs/Twist \
  "{angular: {z: 0.5}}"
```

### 操作4: 编写完整的控制程序

创建 `my_drone_controller.py`:

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, Twist
import math

class DroneController(Node):
    def __init__(self):
        super().__init__('drone_controller')
        
        self.pos_pub = self.create_publisher(
            PoseStamped, '/drone_0/cmd_pose', 10)
        self.vel_pub = self.create_publisher(
            Twist, '/drone_0/cmd_vel', 10)
        
        self.current_pos = None
        
        # 订阅当前位置
        self.sub = self.create_subscription(
            PoseStamped, '/drone_0/pose', 
            self.pose_callback, 10)
    
    def pose_callback(self, msg):
        self.current_pos = msg.pose.position
    
    def go_to(self, x, y, z, timeout=10):
        """飞到指定位置"""
        msg = PoseStamped()
        msg.header.frame_id = 'world'
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.position.z = float(z)
        msg.pose.orientation.w = 1.0
        
        start_time = self.get_clock().now()
        while (self.get_clock().now() - start_time).nanoseconds < timeout * 1e9:
            self.pos_pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.01)
    
    def square_mission(self):
        """执行方形任务"""
        self.get_logger().info('Starting square mission...')
        
        # 起飞
        self.go_to(0, 0, 2)
        
        # 方形巡航
        waypoints = [(2, 0), (2, 2), (0, 2), (0, 0)]
        for x, y in waypoints:
            self.go_to(x, y, 2)
            self.get_logger().info(f'Reached ({x}, {y})')
        
        # 着陆
        self.go_to(0, 0, 0)
        self.get_logger().info('Mission complete!')

def main():
    rclpy.init()
    controller = DroneController()
    
    try:
        controller.square_mission()
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

运行程序：
```bash
python3 my_drone_controller.py
```

## 常见任务

### 任务1: 让无人机自动起飞

```python
# 自动起飞脚本
import rclpy
from geometry_msgs.msg import PoseStamped

rclpy.init()
node = rclpy.create_node('takeoff')
pub = node.create_publisher(PoseStamped, '/drone_0/cmd_pose', 10)

# 发送起飞命令（上升到2米）
for i in range(10):
    msg = PoseStamped()
    msg.header.frame_id = 'world'
    msg.pose.position.z = 2.0
    msg.pose.orientation.w = 1.0
    pub.publish(msg)
    node.get_clock().sleep_for(rclpy.duration.Duration(seconds=0.1))

print("Takeoff command sent!")
rclpy.shutdown()
```

### 任务2: 实时监控无人机高度

```python
import rclpy
from geometry_msgs.msg import PoseStamped

def pose_callback(msg):
    print(f"Altitude: {msg.pose.position.z:.2f} m")

rclpy.init()
node = rclpy.create_node('altitude_monitor')
sub = node.create_subscription(PoseStamped, '/drone_0/pose', pose_callback, 10)
rclpy.spin(node)
```

### 任务3: 记录飞行数据

```bash
# 启动rosbag记录
ros2 bag record /drone_0/pose /drone_0/twist /drone_0/fmu/out/vehicle_status

# 运行无人机任务...

# 回放记录的数据
ros2 bag play rosbag2_YYYY_MM_DD-HH_MM_SS

# 在另一个终端查看回放的数据
ros2 topic echo /drone_0/pose
```

### 任务4: 在RViz中可视化轨迹

```python
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from math import sin, cos, pi

class TrajectoryVisualizer(Node):
    def __init__(self):
        super().__init__('trajectory_visualizer')
        self.marker_pub = self.create_publisher(MarkerArray, '/trajectory', 10)
        
        # 创建圆形轨迹
        markers = MarkerArray()
        for i in range(100):
            angle = 2 * pi * i / 100
            marker = Marker()
            marker.header.frame_id = 'world'
            marker.type = Marker.SPHERE
            marker.pose.position.x = 2 * cos(angle)
            marker.pose.position.y = 2 * sin(angle)
            marker.pose.position.z = 2.0
            marker.scale.x = 0.1
            marker.scale.y = 0.1
            marker.scale.z = 0.1
            marker.color.a = 1.0
            marker.color.r = 1.0
            marker.id = i
            markers.markers.append(marker)
        
        self.marker_pub.publish(markers)

rclpy.init()
node = TrajectoryVisualizer()
rclpy.spin(node)
```

## 故障排查

### 问题1：无人机位置不更新

**症状**: 
```
ros2 topic echo /drone_0/pose
# 无任何输出
```

**诊断步骤**:
1. 检查ROS节点是否运行: `ros2 node list`
2. 检查PX4 SITL是否启动
3. 检查网络连接: `netstat -an | grep 1857`

**解决方案**:
```bash
# 重启所有组件
# 终端A
cd ~/development/PX4-Autopilot && make px4_sitl gazebo

# 终端B
cd ~/FlyControl/ros2_fc && source install/setup.bash
ros2 launch drone_control px4_gazebo.py
```

### 问题2：发送命令无效

**症状**: 发送位置命令后无人机不动

**诊断**:
```bash
# 检查是否进入Offboard模式
ros2 topic echo /drone_0/fmu/out/vehicle_status
# 查看 nav_state 是否为 7 (OFFBOARD)
```

**解决方案**:
- Offboard节点会自动设置Offboard模式和武装
- 确保PX4 Offboard控制器正在运行
- 检查日志: `ros2 node info /px4_offboard_controller`

### 问题3：Gazebo启动缓慢

**症状**: Gazebo启动需要很长时间

**优化**:
```bash
# 清除Gazebo缓存
rm -rf ~/.gazebo

# 降低物理仿真频率
export GAZEBO_REAL_TIME_UPDATE_RATE=100
export GAZEBO_MAX_STEP_SIZE=0.01
```

### 问题4：ROS节点无法通信

**症状**: 节点无法发现彼此

**解决**:
```bash
# 检查ROS_DOMAIN_ID
echo $ROS_DOMAIN_ID

# 设置允许网络通信
export ROS_LOCALHOST_ONLY=0

# 检查daemon
ros2 daemon status
```

## 高级主题

### 集成SLAM

```bash
# 安装SLAM包
sudo apt install ros-humble-rtabmap*

# 启动带SLAM的仿真
ros2 launch drone_control px4_gazebo_slam.launch.xml
```

### 多无人机仿真

修改launch文件以支持多个无人机：
```python
# launch/multi_drone.py
for drone_id in range(3):
    namespace = f'/drone_{drone_id}'
    # 为每个无人机创建节点...
```

### 性能监测

```bash
# 查看系统负载
ros2 topic hz /drone_0/pose

# 查看主题带宽
ros2 topic bw /drone_0/pose

# 使用rqt进行实时监测
ros2 run rqt_plot rqt_plot
```

---

**需要帮助?** 查看 [README.md](README.md) 或 [QUICK_START.md](QUICK_START.md)
