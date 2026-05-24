# ROS2 Humble 虚拟无人机仿真系统

基于PX4 SITL和Gazebo的完整无人机仿真解决方案，集成ROS2 Humble。

## 系统要求

- **操作系统**: Ubuntu 22.04 LTS
- **ROS2**: Humble (需要预先安装)
- **Gazebo**: 11.0+
- **Python**: 3.10+
- **PX4**: v1.14+

## 快速开始

### 1. 前置条件检查

```bash
# 检查ROS2安装
echo $ROS_DISTRO

# 检查Gazebo安装
gazebo --version

# 检查Python版本
python3 --version
```

### 2. 安装依赖

```bash
# 安装系统依赖
sudo apt update
sudo apt install -y \
    gazebo gazebo-dev \
    ros-humble-gazebo-* \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    python3-pip

# 安装Python依赖
pip3 install \
    PyYAML \
    numpy \
    Pillow
```

### 3. 编译项目

```bash
# 进入工作空间
cd ~/FlyControl/ros2_fc

# 编译
colcon build --symlink-install

# 源配置文件
source install/setup.bash
```

### 4. PX4 SITL 安装

```bash
# 克隆PX4代码库
git clone https://github.com/PX4/PX4-Autopilot.git --depth=1 -b v1.14.0
cd PX4-Autopilot

# 安装依赖
bash ./Tools/setup/ubuntu.sh

# 编译SITL
make px4_sitl gazebo
```

### 5. 运行仿真

#### 方式A: 基础仿真

```bash
# Terminal 1: 启动PX4 SITL
cd ~/PX4-Autopilot
make px4_sitl gazebo

# Terminal 2: 启动ROS2节点
cd ~/FlyControl/ros2_fc
source install/setup.bash
ros2 launch drone_control px4_gazebo.py

# Terminal 3: 发送控制命令
cd ~/FlyControl/ros2_fc
source install/setup.bash
ros2 run drone_control px4_offboard
```

#### 方式B: 使用Launch文件

```bash
# 一键启动所有组件
cd ~/FlyControl/ros2_fc
source install/setup.bash
ros2 launch drone_control px4_gazebo.py
```

## 系统架构

```
┌─────────────────────────────────────────┐
│         ROS2 Humble 应用层              │
│  ┌──────────────────────────────────┐  │
│  │  px4_offboard (Offboard控制)    │  │
│  ├──────────────────────────────────┤  │
│  │  drone_state_monitor (状态监控)  │  │
│  ├──────────────────────────────────┤  │
│  │  gazebo_sim_interface (仿真接口) │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
           ↓ (ROS Topics)
┌─────────────────────────────────────────┐
│         PX4 固件层 (Offboard)           │
│  ┌──────────────────────────────────┐  │
│  │   车辆管理系统 (Vehicle Manager)  │  │
│  ├──────────────────────────────────┤  │
│  │   估计器 (Estimator)              │  │
│  ├──────────────────────────────────┤  │
│  │   控制器 (Controller)             │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
           ↓ (UDP/TCP)
┌─────────────────────────────────────────┐
│       Gazebo 仿真环境                   │
│  ┌──────────────────────────────────┐  │
│  │   Iris 四旋翼无人机模型          │  │
│  ├──────────────────────────────────┤  │
│  │   传感器模拟 (IMU, GPS等)        │  │
│  ├──────────────────────────────────┤  │
│  │   物理仿真引擎 (ODE/Bullet)      │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 核心组件说明

### 1. `px4_offboard.py` - PX4 Offboard 控制器

**功能**: 通过Offboard模式控制无人机

**订阅主题**:
- `/drone_0/cmd_vel` - 速度命令 (geometry_msgs/Twist)
- `/drone_0/cmd_pose` - 位置命令 (geometry_msgs/PoseStamped)
- `/drone_0/fmu/out/vehicle_status` - 无人机状态
- `/drone_0/fmu/out/vehicle_local_position` - 本地位置

**发布主题**:
- `/drone_0/fmu/in/offboard_control_mode` - 控制模式
- `/drone_0/fmu/in/trajectory_setpoint` - 轨迹设置点
- `/drone_0/fmu/in/vehicle_command` - 车辆命令

**关键方法**:
```python
arm()                    # 武装无人机
disarm()                 # 解除武装
set_offboard_mode()      # 设置Offboard模式
```

### 2. `drone_state_monitor.py` - 状态监控

**功能**: 发布无人机的实时状态信息

**订阅主题**:
- `/drone_0/fmu/out/vehicle_status` - 车辆状态
- `/drone_0/fmu/out/vehicle_local_position` - 本地位置
- `/drone_0/fmu/out/sensor_combined` - 传感器数据

**发布主题**:
- `/drone_0/pose` - 位置姿态 (geometry_msgs/PoseStamped)
- `/drone_0/twist` - 速度 (geometry_msgs/TwistStamped)
- `/drone_0/accel` - 加速度 (geometry_msgs/AccelStamped)
- `/drone_0/imu` - IMU数据 (sensor_msgs/Imu)
- `/drone_0/odom` - 里程计 (nav_msgs/Odometry)

### 3. `gazebo_sim_interface.py` - Gazebo接口

**功能**: 连接Gazebo仿真和ROS2系统

**配置参数**:
```yaml
vehicle_id: 0                    # 无人机ID
enable_ground_truth: true        # 启用地面真实数据
sim_model_name: iris             # 模型名称
```

## 常用命令

### 查看主题列表

```bash
ros2 topic list
```

### 监听特定主题

```bash
# 查看无人机位置
ros2 topic echo /drone_0/pose

# 查看无人机状态
ros2 topic echo /drone_0/fmu/out/vehicle_status
```

### 发送命令

```bash
# 发送位置命令
ros2 topic pub /drone_0/cmd_pose geometry_msgs/PoseStamped \
  "{header: {frame_id: 'world'}, pose: {position: {x: 1.0, y: 1.0, z: 2.0}, orientation: {w: 1.0}}}"

# 发送速度命令
ros2 topic pub /drone_0/cmd_vel geometry_msgs/Twist \
  "{linear: {x: 0.1, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

### 调试信息

```bash
# 查看节点信息
ros2 node list
ros2 node info /px4_offboard_controller

# 查看服务列表
ros2 service list

# 查看参数
ros2 param list
ros2 param get /px4_offboard_controller vehicle_id
```

## 配置文件

### `config/px4_config.yaml`

```yaml
# 通信配置
sitl_udp_port: 18570
ros_namespace: drone_0

# 飞行器配置  
vehicle_type: quadrotor
vehicle_model: iris

# 传感器配置
gps:
  enabled: true
  lat0: 47.397742    # 初始纬度
  lon0: 8.545594     # 初始经度
  alt0: 488          # 初始高度

# 控制配置
control_mode: offboard
max_roll: 45.0       # 最大滚转角 (度)
max_pitch: 45.0      # 最大俯仰角 (度)
max_yaw_rate: 90.0   # 最大偏航角速率 (度/秒)
```

## 常见问题

### Q1: PX4 SITL启动失败

**解决方案**:
```bash
# 检查PX4编译
cd ~/PX4-Autopilot
make px4_sitl_default gazebo

# 检查gazebo插件路径
echo $GAZEBO_PLUGIN_PATH
echo $GAZEBO_MODEL_PATH

# 添加路径到.bashrc
export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:~/PX4-Autopilot/build/px4_sitl_default/build_gazebo
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:~/PX4-Autopilot/Tools/simulation/gazebo/sitl_gazebo/models
```

### Q2: ROS2节点无法连接PX4

**解决方案**:
```bash
# 检查网络通信
netstat -an | grep 1857

# 检查ROS_DOMAIN_ID
echo $ROS_DOMAIN_ID

# 手动设置
export ROS_DOMAIN_ID=0
```

### Q3: Gazebo窗口不显示

**解决方案**:
```bash
# 检查显示设置
echo $DISPLAY

# 如果是远程连接，使用VNC或X11转发
export DISPLAY=:0
```

## 扩展开发

### 添加自定义传感器

```python
# 在 drone_state_monitor.py 中添加
self.camera_sub = self.create_subscription(
    Image,
    f'{self.namespace}/camera/image',
    self.camera_callback,
    10
)

def camera_callback(self, msg: Image):
    # 处理相机图像
    pass
```

### 实现轨迹规划

```python
# 创建新的轨迹规划器节点
class TrajectoryPlanner(Node):
    def trajectory_callback(self, msg):
        # 生成轨迹
        trajectory = self.plan_trajectory(msg)
        self.trajectory_pub.publish(trajectory)
```

### 与SLAM集成

```bash
ros2 launch drone_control integrated_slam_launch.py
```

## 参考资源

- [PX4官方文档](https://docs.px4.io/)
- [ROS2 Humble文档](https://docs.ros.org/en/humble/)
- [Gazebo官方文档](http://gazebosim.org/tutorials/)
- [PX4与ROS2集成](https://docs.px4.io/main/en/ros/ros2.html)

## 许可证

Apache License 2.0

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题，请联系维护者：ywt@todo.todo
