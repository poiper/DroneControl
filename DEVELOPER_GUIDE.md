# 虚拟无人机系统开发者指南

## 概述

本指南为开发者提供了扩展和定制虚拟无人机系统的方法。

## 项目结构

```
drone_control/
├── drone_control/              # Python源包
│   ├── __init__.py
│   ├── px4_offboard.py         # Offboard控制器
│   ├── drone_state_monitor.py  # 状态监控
│   └── gazebo_sim_interface.py # Gazebo接口
│
├── launch/                     # ROS2 launch文件
│   ├── px4_gazebo.py          # Python launch
│   └── px4_gazebo.launch.xml   # XML launch
│
├── config/                     # 配置文件
│   └── px4_config.yaml
│
├── worlds/                     # Gazebo世界文件
│   └── empty_world.world
│
├── models/                     # 自定义模型（可选）
│
├── package.xml                # ROS2包描述
├── setup.py                   # Python安装脚本
├── setup.cfg                  # Python配置
└── README.md                  # 文档
```

## 添加新的ROS节点

### 示例：创建轨迹规划器

**步骤1**: 创建新文件 `drone_control/trajectory_planner.py`

```python
#!/usr/bin/env python3
"""
轨迹规划器节点
生成平滑的飞行轨迹
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import numpy as np
from scipy.interpolate import interp1d


class TrajectoryPlanner(Node):
    """轨迹规划器"""
    
    def __init__(self):
        super().__init__('trajectory_planner')
        
        self.declare_parameter('namespace', '/drone_0')
        self.declare_parameter('trajectory_type', 'line')
        
        self.namespace = self.get_parameter('namespace').value
        self.trajectory_type = self.get_parameter('trajectory_type').value
        
        # 发布器
        self.trajectory_pub = self.create_publisher(
            PoseStamped,
            f'{self.namespace}/planned_trajectory',
            10
        )
        
        # 定时器
        self.timer = self.create_timer(0.1, self.timer_callback)
        self.time_step = 0
        
        self.get_logger().info(
            f'Trajectory Planner initialized '
            f'(type={self.trajectory_type})'
        )
    
    def generate_line_trajectory(self, t):
        """生成直线轨迹"""
        x = t * 0.1
        y = 0.0
        z = 2.0
        return np.array([x, y, z])
    
    def generate_circle_trajectory(self, t):
        """生成圆形轨迹"""
        radius = 2.0
        angular_velocity = 0.5
        angle = angular_velocity * t
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        z = 2.0
        return np.array([x, y, z])
    
    def generate_helix_trajectory(self, t):
        """生成螺旋轨迹"""
        radius = 2.0
        angular_velocity = 0.5
        vertical_velocity = 0.1
        angle = angular_velocity * t
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        z = 2.0 + vertical_velocity * t
        return np.array([x, y, z])
    
    def timer_callback(self):
        """定时发布轨迹"""
        if self.trajectory_type == 'line':
            pos = self.generate_line_trajectory(self.time_step)
        elif self.trajectory_type == 'circle':
            pos = self.generate_circle_trajectory(self.time_step)
        elif self.trajectory_type == 'helix':
            pos = self.generate_helix_trajectory(self.time_step)
        else:
            pos = np.array([0.0, 0.0, 2.0])
        
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'world'
        msg.pose.position.x = float(pos[0])
        msg.pose.position.y = float(pos[1])
        msg.pose.position.z = float(pos[2])
        msg.pose.orientation.w = 1.0
        
        self.trajectory_pub.publish(msg)
        self.time_step += 0.1


def main(args=None):
    rclpy.init(args=args)
    planner = TrajectoryPlanner()
    rclpy.spin(planner)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

**步骤2**: 更新 `setup.py`

```python
entry_points={
    'console_scripts': [
        'talker = drone_control.talker:main',
        'px4_offboard = drone_control.px4_offboard:main',
        'drone_state_monitor = drone_control.drone_state_monitor:main',
        'gazebo_sim_interface = drone_control.gazebo_sim_interface:main',
        'trajectory_planner = drone_control.trajectory_planner:main',  # 添加这行
    ],
},
```

**步骤3**: 编译并运行

```bash
cd ~/FlyControl/ros2_fc
colcon build --symlink-install
source install/setup.bash

# 运行轨迹规划器
ros2 run drone_control trajectory_planner --ros-args -p trajectory_type:=circle
```

## 创建自定义Launch文件

### 示例：多无人机launch文件

`launch/multi_drone_gazebo.py`:

```python
#!/usr/bin/env python3
"""
多无人机Gazebo仿真Launch文件
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
import os

def generate_launch_description():
    ld = LaunchDescription()
    
    # 启动Gazebo
    gazebo = ExecuteProcess(
        cmd=['gazebo', '--verbose', 'worlds/empty.world'],
        output='screen'
    )
    ld.add_action(gazebo)
    
    # 为3个无人机创建节点
    for drone_id in range(3):
        namespace = f'/drone_{drone_id}'
        
        # 状态监控
        state_monitor = Node(
            package='drone_control',
            executable='drone_state_monitor',
            output='screen',
            parameters=[{
                'vehicle_id': drone_id,
                'namespace': namespace,
            }]
        )
        ld.add_action(state_monitor)
        
        # Offboard控制
        offboard = Node(
            package='drone_control',
            executable='px4_offboard',
            output='screen',
            parameters=[{
                'vehicle_id': drone_id,
                'namespace': namespace,
            }]
        )
        ld.add_action(offboard)
    
    return ld
```

使用：
```bash
ros2 launch drone_control multi_drone_gazebo.py
```

## 添加自定义Gazebo模型

### 创建Iris无人机的自定义版本

**步骤1**: 创建模型目录

```bash
mkdir -p ~/FlyControl/ros2_fc/src/drone_control/models/custom_iris
cd ~/FlyControl/ros2_fc/src/drone_control/models/custom_iris
```

**步骤2**: 创建 `model.config`

```xml
<?xml version="1.0"?>
<model>
  <name>Custom Iris</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>
  <author>
    <name>Your Name</name>
    <email>your.email@example.com</email>
  </author>
  <description>
    Customized Iris quadrotor for ROS2 simulation
  </description>
</model>
```

**步骤3**: 创建 `model.sdf` 

（这是一个复杂的文件，通常复制自PX4-Autopilot）

## 与SLAM系统集成

### ORB-SLAM3集成

**步骤1**: 安装ORB-SLAM3

```bash
# 下载并编译
git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git
cd ORB_SLAM3
./build.sh
```

**步骤2**: 创建SLAM节点 `drone_control/slam_interface.py`

```python
#!/usr/bin/env python3
"""
SLAM接口节点
连接ORB-SLAM3和无人机控制
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
import cv2
import numpy as np


class SLAMInterface(Node):
    """SLAM接口"""
    
    def __init__(self):
        super().__init__('slam_interface')
        
        # 订阅相机图像（模拟或真实）
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image',
            self.image_callback,
            10
        )
        
        # 发布位姿估计
        self.pose_pub = self.create_publisher(
            PoseStamped,
            '/drone_0/slam_pose',
            10
        )
        
        # 发布里程计
        self.odom_pub = self.create_publisher(
            Odometry,
            '/drone_0/slam_odom',
            10
        )
    
    def image_callback(self, msg: Image):
        """处理图像"""
        # 在这里集成ORB-SLAM3处理
        # 1. 转换ROS Image消息到OpenCV格式
        # 2. 输入到ORB-SLAM3
        # 3. 获取位姿估计
        # 4. 发布结果
        
        # 示例：发布固定位姿
        pose_msg = PoseStamped()
        pose_msg.header.frame_id = 'world'
        pose_msg.pose.position.x = 0.0
        pose_msg.pose.position.y = 0.0
        pose_msg.pose.position.z = 0.0
        pose_msg.pose.orientation.w = 1.0
        
        self.pose_pub.publish(pose_msg)


def main(args=None):
    rclpy.init(args=args)
    interface = SLAMInterface()
    rclpy.spin(interface)


if __name__ == '__main__':
    main()
```

## 性能优化

### 1. 编译优化

```bash
# Release模式编译
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release --symlink-install

# 并行编译
colcon build -j 8 --symlink-install
```

### 2. ROS参数优化

```bash
# 提高通信优先级
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0

# 禁用日志
export RCUTILS_LOGGING_USE_STDOUT=0
```

### 3. Gazebo优化

```bash
# 降低物理更新频率
export GAZEBO_REAL_TIME_UPDATE_RATE=100

# 禁用某些物理计算
# 在Gazebo配置文件中修改
```

## 单元测试

### 创建测试 `test/test_offboard.py`

```python
#!/usr/bin/env python3
"""
Offboard控制器的单元测试
"""

import unittest
import rclpy
from drone_control.px4_offboard import PX4OffboardController


class TestOffboardController(unittest.TestCase):
    """测试Offboard控制器"""
    
    def setUp(self):
        """测试前准备"""
        rclpy.init()
    
    def tearDown(self):
        """测试后清理"""
        rclpy.shutdown()
    
    def test_arm_disarm(self):
        """测试武装/解除武装"""
        controller = PX4OffboardController()
        
        # 测试武装
        controller.arm()
        # 验证状态...
        
        # 测试解除武装
        controller.disarm()
        # 验证状态...


if __name__ == '__main__':
    unittest.main()
```

运行测试：
```bash
python3 -m pytest test/test_offboard.py
```

## 文档更新

当添加新功能时，请更新：

1. **README.md** - 添加功能说明
2. **USER_GUIDE.md** - 添加使用示例
3. **代码注释** - 添加docstring
4. **CHANGELOG.md** - 记录更新

## 贡献流程

1. 创建功能分支：`git checkout -b feature/your-feature`
2. 开发并测试功能
3. 提交变更：`git commit -am "Add feature"`
4. 推送分支：`git push origin feature/your-feature`
5. 创建Pull Request

## 常见扩展点

### 1. 添加新的控制模式

在 `px4_offboard.py` 中添加新的控制方法：

```python
def set_manual_mode(self):
    """设置手动模式"""
    # 实现...

def set_position_control_mode(self):
    """设置位置控制模式"""
    # 实现...
```

### 2. 集成新的传感器

在 `drone_state_monitor.py` 中添加：

```python
self.lidar_sub = self.create_subscription(
    LaserScan,
    f'{self.namespace}/scan',
    self.lidar_callback,
    10
)

def lidar_callback(self, msg: LaserScan):
    # 处理激光雷达数据
    pass
```

### 3. 实现路径追踪

```python
class PathTracker(Node):
    def __init__(self):
        super().__init__('path_tracker')
        # 实现路径追踪逻辑
        self.timer = self.create_timer(0.01, self.tracking_loop)
    
    def tracking_loop(self):
        # 计算控制输入
        # 发送给Offboard控制器
        pass
```

## 调试技巧

### 1. 启用详细日志

```python
# 在节点中
self.get_logger().set_level(rclpy.logging.LoggingSeverity.DEBUG)
```

### 2. 使用rqt工具

```bash
# 查看节点图
ros2 run rqt_graph rqt_graph

# 查看日志
ros2 run rqt_console rqt_console

# 实时绘图
ros2 run rqt_plot rqt_plot

# 动态配置
ros2 run rqt_reconfigure rqt_reconfigure
```

### 3. 记录和回放

```bash
# 记录所有主题
ros2 bag record -a

# 回放
ros2 bag play rosbag2_YYYY_MM_DD-HH_MM_SS
```

## 性能分析

```bash
# 使用cProfile分析Python代码
python3 -m cProfile -s cumtime my_script.py

# 使用tracemalloc分析内存
python3 -X dev my_script.py
```

## 参考资源

- [ROS2 Humble 开发者指南](https://docs.ros.org/en/humble/Tutorials.html)
- [PX4 开发者文档](https://docs.px4.io/)
- [Gazebo 插件开发](http://gazebosim.org/tutorials/)
- [Python最佳实践](https://pep8.org/)

---

有问题？提交Issue或查看完整文档！
