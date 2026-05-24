# ROS2 Humble 虚拟无人机仿真系统

![System Architecture](https://img.shields.io/badge/ROS2-Humble-blue) ![PX4](https://img.shields.io/badge/PX4-SITL-red) ![Gazebo](https://img.shields.io/badge/Gazebo-11-green)

完整的基于ROS2 Humble、PX4 SITL和Gazebo的虚拟无人机仿真系统，支持Offboard模式控制。

## 📋 快速目录

- [主要特性](#主要特性)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [文档](#文档)
- [常见问题](#常见问题)

## 🚀 主要特性

### 核心功能
- ✅ **PX4 SITL仿真** - 完整的PX4固件仿真
- ✅ **Gazebo物理仿真** - 真实的物理环境
- ✅ **ROS2集成** - 现代机器人操作系统
- ✅ **Offboard控制** - 外部计算机控制无人机
- ✅ **完整API** - 位置控制、速度控制、状态监控

### 系统特点
- 🎯 **模块化设计** - 易于扩展和定制
- 📊 **完整的状态监控** - 实时获取所有飞行数据
- 🔧 **开箱即用** - 一键启动完整系统
- 📚 **详细文档** - 包含用户指南和开发指南
- 🧪 **系统检测工具** - 验证环境和依赖

## 💻 系统要求

| 项目 | 最小要求 | 推荐配置 |
|------|--------|--------|
| **操作系统** | Ubuntu 22.04 | Ubuntu 22.04 LTS |
| **ROS2** | Humble | Humble |
| **Python** | 3.10+ | 3.10+ |
| **Gazebo** | 11.0+ | 11.0+ |
| **CPU** | 4核 | 8核+ |
| **内存** | 4GB | 8GB+ |
| **硬盘** | 10GB | 20GB+ |

## 🎯 快速开始

### 方式1：使用自动脚本（推荐）

```bash
# 1. 验证系统环境
python3 ~/FlyControl/ros2_fc/test_system.py

# 2. 3个终端启动系统
# Terminal A: PX4 SITL
cd ~/development/PX4-Autopilot
make px4_sitl gazebo

# Terminal B: ROS2节点
cd ~/FlyControl/ros2_fc && source install/setup.bash
ros2 launch drone_control px4_gazebo.py

# Terminal C: 验证
ros2 topic echo /drone_0/pose
```

### 方式2：详细安装步骤

请参考 [INSTALL.md](INSTALL.md) 获取完整的安装指南。

## 📚 文档

### 用户文档
- **[USER_GUIDE.md](USER_GUIDE.md)** - 完整的用户指南
  - 系统概述和架构
  - 详细的操作步骤
  - 常见任务示例
  - 故障排查

- **[QUICK_START.md](QUICK_START.md)** - 快速参考
  - 一键命令
  - 主题和参数
  - 常用工具

- **[FLIGHT_OPERATION.md](FLIGHT_OPERATION.md)** - 飞行操作说明
  - 启动 PX4 SITL、Gazebo 和 ROS2 节点
  - 使用 ROS2 话题让飞机起飞
  - 查看飞行状态和常见问题排查

### 开发文档
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - 开发者指南
  - 项目结构
  - 添加新节点
  - 扩展系统
  - 性能优化

### 安装和配置
- **[INSTALL.md](INSTALL.md)** - 完整安装指南
  - 环境准备
  - 依赖安装
  - PX4编译
  - 故障排除

## 🏗️ 系统架构

```
┌─────────────────────────────────────────┐
│      ROS2 应用层                        │
│  ┌──────────────────────────────────┐  │
│  │  Offboard 控制器                 │  │
│  │  ├─ 位置控制                     │  │
│  │  ├─ 速度控制                     │  │
│  │  └─ 模式管理                     │  │
│  ├──────────────────────────────────┤  │
│  │  状态监控                        │  │
│  │  ├─ 位置/速度发布               │  │
│  │  ├─ IMU数据发布                 │  │
│  │  └─ 里程计发布                  │  │
│  └──────────────────────────────────┘  │
└────────────┬────────────────────────────┘
             │ ROS主题/服务
┌────────────▼────────────────────────────┐
│      PX4 Autopilot (Offboard)          │
│  ├─ 车辆管理系统                       │
│  ├─ 位置/速度估计器                    │
│  ├─ 姿态控制器                         │
│  └─ 电机混合器                         │
└────────────┬────────────────────────────┘
             │ SITL (UDP)
┌────────────▼────────────────────────────┐
│      Gazebo 仿真环境                    │
│  ├─ Iris 四旋翼模型                    │
│  ├─ 虚拟传感器 (IMU/GPS)              │
│  ├─ 物理引擎 (ODE)                     │
│  └─ 环境条件 (风/重力)                 │
└─────────────────────────────────────────┘
```

## 🔑 核心组件

### 1. px4_offboard.py - Offboard控制器

提供ROS2接口控制无人机。

**功能**:
- 位置控制 (SetpointPosition)
- 速度控制 (SetpointVelocity)
- 武装/解除武装
- 模式切换

**使用示例**:
```bash
# 发送位置命令
ros2 topic pub /drone_0/cmd_pose geometry_msgs/PoseStamped \
  "{header: {frame_id: 'world'}, pose: {position: {x: 1.0, y: 1.0, z: 2.0}, orientation: {w: 1.0}}}"
```

### 2. drone_state_monitor.py - 状态监控

实时发布无人机状态信息。

**发布的主题**:
- `/drone_0/pose` - 位置和姿态
- `/drone_0/twist` - 速度
- `/drone_0/accel` - 加速度
- `/drone_0/imu` - IMU数据
- `/drone_0/odom` - 里程计

### 3. gazebo_sim_interface.py - Gazebo接口

连接Gazebo仿真环境和ROS2。

## 📊 系统消息流

```
用户应用
  ↓
ROS2主题 (/drone_0/cmd_pose)
  ↓
px4_offboard节点
  ↓
PX4消息 (TrajectorySetpoint)
  ↓
PX4固件
  ↓
电机命令 (ActuatorMotors)
  ↓
Gazebo仿真
  ↓
虚拟传感器
  ↓
PX4估计器
  ↓
drone_state_monitor
  ↓
ROS2主题 (/drone_0/pose, etc)
  ↓
用户应用
```

## 🚄 性能指标

| 指标 | 值 |
|------|-----|
| 位置更新频率 | 50 Hz |
| Offboard控制频率 | 100 Hz |
| 传感器仿真频率 | 250 Hz |
| 物理仿真步长 | 0.004 s |
| 典型CPU占用 | 40-60% (4核) |

## 🎓 使用示例

### 示例1：简单的飞行任务

```python
import rclpy
from geometry_msgs.msg import PoseStamped

rclpy.init()
node = rclpy.create_node('simple_flight')
pub = node.create_publisher(PoseStamped, '/drone_0/cmd_pose', 10)

# 起飞到2米
msg = PoseStamped()
msg.header.frame_id = 'world'
msg.pose.position.z = 2.0
msg.pose.orientation.w = 1.0

for i in range(100):
    pub.publish(msg)
    node.get_clock().sleep_for(rclpy.duration.Duration(seconds=0.1))

rclpy.shutdown()
```

### 示例2：监控无人机状态

```bash
# 实时查看位置
ros2 topic echo /drone_0/pose

# 查看飞行状态
ros2 topic echo /drone_0/fmu/out/vehicle_status

# 使用RViz可视化
ros2 run rviz2 rviz2
# 添加 /drone_0/pose 和 /drone_0/odom
```

### 示例3：完整的控制程序

请参考 [USER_GUIDE.md](USER_GUIDE.md) 中的"完整的控制程序"部分。

## 🛠️ 常见命令

```bash
# 编译项目
cd ~/FlyControl/ros2_fc && colcon build --symlink-install

# 运行系统检测
python3 ~/FlyControl/ros2_fc/test_system.py

# 启动Gazebo + PX4 + ROS2
# 见快速开始部分

# 查看所有ROS节点
ros2 node list

# 查看所有主题
ros2 topic list

# 记录飞行数据
ros2 bag record /drone_0/pose /drone_0/twist

# 回放数据
ros2 bag play rosbag2_YYYY_MM_DD-HH_MM_SS
```

## ❓ 常见问题

### Q1: PX4 SITL启动失败

**解决方案**:
```bash
# 检查编译
cd ~/development/PX4-Autopilot
make clean
make px4_sitl gazebo

# 检查插件路径
echo $GAZEBO_PLUGIN_PATH
```

详细答案见 [INSTALL.md](INSTALL.md) 的故障排除部分。

### Q2: 无人机位置不更新

**原因**: 可能是Offboard节点未启动或PX4未进入Offboard模式

**解决方案**:
```bash
# 检查节点运行状态
ros2 node list

# 检查是否在Offboard模式
ros2 topic echo /drone_0/fmu/out/vehicle_status
```

### Q3: 仿真运行缓慢

**原因**: 可能是Gazebo物理仿真设置过高

**优化**:
```bash
export GAZEBO_REAL_TIME_UPDATE_RATE=100
export GAZEBO_MAX_STEP_SIZE=0.01
```

详见 [QUICK_START.md](QUICK_START.md#性能监控)

## 🔧 故障排除

系统包含自动故障检测工具：

```bash
# 运行完整诊断
python3 ~/FlyControl/ros2_fc/test_system.py

# 该工具将检查：
# ✓ ROS2环境
# ✓ Gazebo安装
# ✓ PX4 SITL编译
# ✓ ROS包依赖
# ✓ 网络配置
# ✓ 等等...
```

## 📦 项目结构

```
FlyControl/
└── ros2_fc/
    ├── src/
    │   └── drone_control/
    │       ├── drone_control/      # Python包
    │       ├── launch/             # ROS2启动文件
    │       ├── config/             # 配置文件
    │       ├── worlds/             # Gazebo世界
    │       ├── models/             # 自定义模型
    │       ├── package.xml         # ROS2包文件
    │       ├── setup.py            # Python安装
    │       └── README.md           # 包文档
    ├── install/                    # 编译输出
    ├── build/                      # 构建文件
    ├── INSTALL.md                  # 安装指南
    ├── USER_GUIDE.md               # 用户指南
    ├── QUICK_START.md              # 快速参考
    ├── DEVELOPER_GUIDE.md          # 开发指南
    └── test_system.py              # 诊断工具
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork此仓库
2. 创建功能分支
3. 提交变更
4. 创建Pull Request

详见 [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#贡献流程)

## 📖 更多资源

### 官方文档
- [ROS2 Humble文档](https://docs.ros.org/en/humble/)
- [PX4官方文档](https://docs.px4.io/)
- [Gazebo官方网站](http://gazebosim.org/)

### 有用的工具
- `ros2 topic` - 管理ROS主题
- `ros2 node` - 管理ROS节点
- `rqt_*` - ROS可视化工具
- `ros2 bag` - 数据记录和回放

## 📝 许可证

Apache License 2.0 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

**维护者**: ywt  
**邮箱**: ywt@todo.todo

## 🙏 致谢

感谢以下项目的支持：
- [ROS2 Project](https://www.ros.org/)
- [PX4 Project](https://px4.io/)
- [Gazebo Project](http://gazebosim.org/)

## 📞 技术支持

遇到问题？
1. 查看 [USER_GUIDE.md](USER_GUIDE.md) 和 [QUICK_START.md](QUICK_START.md)
2. 运行 `python3 test_system.py` 检查系统
3. 检查日志文件 `~/.ros/`
4. 提交Issue或联系维护者

---

**开始使用**: 👉 [快速开始](#快速开始) | **文档**: 📚 [USER_GUIDE.md](USER_GUIDE.md) | **开发**: 🔧 [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

**最后更新**: 2026年5月22日 | **版本**: 0.0.1 | **状态**: 🟢 活跃开发
