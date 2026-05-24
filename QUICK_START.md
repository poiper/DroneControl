# 虚拟无人机系统快速参考

## 一键命令

### 编译
```bash
cd ~/FlyControl/ros2_fc && colcon build --symlink-install
```

### 启动完整仿真
```bash
# Terminal 1: PX4 SITL
cd ~/development/PX4-Autopilot && make px4_sitl gazebo

# Terminal 2: ROS2启动
cd ~/FlyControl/ros2_fc && source install/setup.bash && ros2 launch drone_control px4_gazebo.py
```

## ROS主题快速参考

### 监听主题
| 命令 | 作用 |
|------|------|
| `ros2 topic echo /drone_0/pose` | 查看无人机位置 |
| `ros2 topic echo /drone_0/twist` | 查看速度信息 |
| `ros2 topic echo /drone_0/fmu/out/vehicle_status` | 查看飞行状态 |

### 发布命令
| 命令 | 作用 |
|------|------|
| `ros2 topic pub /drone_0/cmd_pose geometry_msgs/PoseStamped ...` | 位置控制 |
| `ros2 topic pub /drone_0/cmd_vel geometry_msgs/Twist ...` | 速度控制 |

## 关键参数

### PX4配置 (`config/px4_config.yaml`)
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `sitl_udp_port` | 18570 | SITL通信端口 |
| `ros_namespace` | drone_0 | ROS命名空间 |
| `vehicle_model` | iris | 无人机模型 |
| `max_roll` | 45.0° | 最大滚转角 |

### Offboard控制器参数
```yaml
vehicle_id: 0              # 无人机编号
arm_timeout: 10.0          # 武装超时
namespace: /drone_0        # ROS命名空间
```

## 无人机状态代码

### 飞行状态 (nav_state)
| 值 | 含义 |
|----|------|
| 0 | MANUAL - 手动 |
| 2 | POSCTL - 位置控制 |
| 3 | AUTO_MISSION - 自动任务 |
| 7 | OFFBOARD - 外部控制 |
| 10 | AUTO_TAKEOFF - 自动起飞 |
| 11 | AUTO_LAND - 自动着陆 |

### 武装状态 (arming_state)
| 值 | 含义 |
|----|------|
| 0 | DISARMED - 未武装 |
| 1 | ARMED - 已武装 |
| 2 | ARMED_ERROR - 武装错误 |

## 调试命令

```bash
# 查看所有ROS节点
ros2 node list

# 查看所有主题
ros2 topic list

# 查看主题详情
ros2 topic info /drone_0/pose

# 查看节点详情
ros2 node info /px4_offboard_controller

# 查看参数
ros2 param list
ros2 param get /px4_offboard_controller vehicle_id

# 查看服务
ros2 service list

# 记录数据包
ros2 bag record /drone_0/pose /drone_0/twist

# 回放数据包
ros2 bag play rosbag2_YYYY_MM_DD-HH_MM_SS
```

## 常用Python示例

### 发送位置命令
```python
from geometry_msgs.msg import PoseStamped

msg = PoseStamped()
msg.header.frame_id = 'world'
msg.pose.position.x = 1.0
msg.pose.position.y = 1.0
msg.pose.position.z = 2.0
msg.pose.orientation.w = 1.0

publisher.publish(msg)
```

### 发送速度命令
```python
from geometry_msgs.msg import Twist

msg = Twist()
msg.linear.x = 0.5    # 前进
msg.linear.z = 0.1    # 上升
msg.angular.z = 0.1   # 偏航

publisher.publish(msg)
```

## 文件结构

```
src/drone_control/
├── launch/              # 启动文件
│   ├── px4_gazebo.py
│   └── px4_gazebo.launch.xml
├── config/              # 配置文件
│   └── px4_config.yaml
├── worlds/              # Gazebo世界文件
│   └── empty_world.world
├── drone_control/       # Python源码
│   ├── __init__.py
│   ├── px4_offboard.py        # Offboard控制器
│   ├── drone_state_monitor.py # 状态监控
│   └── gazebo_sim_interface.py # Gazebo接口
├── package.xml
├── setup.py
└── README.md
```

## 端口配置

| 端口 | 协议 | 用途 |
|------|------|------|
| 14550 | UDP | PX4 MAVLINK |
| 18570 | UDP | SITL通信 |
| 14540 | UDP | Gazebo桥接 |

## 图形化工具

### RViz可视化
```bash
ros2 run rviz2 rviz2
# 添加/drone_0/pose主题
```

### rqt_graph查看节点图
```bash
ros2 run rqt_graph rqt_graph
```

### rqt_console查看日志
```bash
ros2 run rqt_console rqt_console
```

## 性能监控

```bash
# CPU/内存使用
top

# ROS网络性能
ros2 topic bw /drone_0/pose
ros2 topic hz /drone_0/pose

# Gazebo性能
# 在Gazebo中按Ctrl+Shift+Z查看统计信息
```

## 环境变量

```bash
# 设置后添加到~/.bashrc

# ROS2配置
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0

# Gazebo配置
export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:~/development/PX4-Autopilot/build/px4_sitl_default/build_gazebo
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:~/development/PX4-Autopilot/Tools/simulation/gazebo/sitl_gazebo/models

# 仿真时间
export GAZEBO_REAL_TIME_UPDATE_RATE=100
export GAZEBO_MAX_STEP_SIZE=0.01
```

## 常见快捷键

### RViz
- `Shift + 左键` - 旋转视角
- `中键` - 移动视角
- `滚轮` - 缩放
- `R` - 重置视角

### Gazebo
- `Ctrl + Shift + Z` - 显示统计信息
- `T` - 翻译工具
- `R` - 旋转工具
- `S` - 缩放工具

## 下一步学习

1. **轨迹规划**: 学习使用CHOMP或Ompl规划无人机轨迹
2. **SLAM集成**: 与ORB-SLAM3或其他SLAM系统集成
3. **多无人机**: 扩展到多无人机编队控制
4. **传感器集成**: 添加激光雷达、相机等传感器模型
5. **高级控制**: 实现模型预测控制(MPC)或强化学习控制

## 故障快速排查

| 症状 | 可能原因 | 解决方案 |
|------|--------|--------|
| 节点无法连接 | 网络隔离 | `export ROS_LOCALHOST_ONLY=0` |
| 主题无数据 | 节点未运行 | `ros2 node list` 检查节点 |
| PX4启动失败 | 编译错误 | 重新编译PX4 |
| Gazebo卡顿 | 性能不足 | 降低更新频率或禁用物理 |
| SITL未启动 | 端口占用 | `lsof -i :18570` 检查 |

---

更多信息请参考 [README.md](README.md) 和 [INSTALL.md](../INSTALL.md)
