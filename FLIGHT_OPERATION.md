# ROS2 + PX4 SITL + Gazebo 飞行操作说明

本文档说明如何启动当前虚拟无人机工程，并通过 ROS2 话题让 Gazebo 中的 PX4 SITL 无人机起飞、悬停和查看状态。

## 1. 系统组成

本工程由三部分组成：

| 组件 | 作用 | 启动方式 |
|------|------|----------|
| PX4 SITL | 运行虚拟飞控固件 | `make px4_sitl gazebo` |
| Gazebo | 显示无人机和物理仿真环境 | 通常由 PX4 SITL 自动启动 |
| ROS2 节点 | 发布控制命令、读取飞控状态 | `ros2 launch drone_control px4_gazebo.py` |

数据流如下：

```text
用户命令
  -> /drone_0/cmd_pose 或 /drone_0/cmd_vel
  -> px4_offboard 节点
  -> /drone_0/fmu/in/trajectory_setpoint
  -> PX4 Offboard 控制
  -> Gazebo 中的无人机运动
  -> /drone_0/fmu/out/vehicle_local_position
  -> drone_state_monitor 节点
  -> /drone_0/pose, /drone_0/twist, /drone_0/odom
```

## 2. launch 文件的作用

ROS2 launch 文件是启动配置脚本，用一条命令启动多个 ROS2 节点并传入参数。

当前 launch 文件位置：

```text
src/drone_control/launch/px4_gazebo.py
```

默认启动以下 ROS2 节点：

| 节点 | 功能 |
|------|------|
| `drone_state_monitor` | 监听 PX4 状态，并发布标准 ROS2 位姿、速度、里程计话题 |
| `gazebo_sim_interface` | Gazebo 接口预留节点 |
| `px4_offboard` | 接收 `/drone_0/cmd_pose` 或 `/drone_0/cmd_vel`，并向 PX4 发送 Offboard 控制命令 |

默认情况下，`px4_gazebo.py` 不再重复启动 PX4 和 Gazebo。推荐先用 PX4 官方命令启动仿真，再用 launch 启动 ROS2 控制节点。

## 3. 启动步骤

### 3.1 编译工程

```bash
cd ~/FlyControl/ros2_fc
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 3.2 启动 PX4 SITL 和 Gazebo

打开第一个终端：

```bash
cd ~/development/PX4-Autopilot
make px4_sitl gazebo
```

等待 Gazebo 窗口出现，并确认能看到无人机模型。

### 3.3 启动 ROS2 控制节点

打开第二个终端：

```bash
cd ~/FlyControl/ros2_fc
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch drone_control px4_gazebo.py
```

### 3.4 检查 PX4 话题

打开第三个终端：

```bash
cd ~/FlyControl/ros2_fc
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic list | grep fmu
```

正常情况下应该看到类似话题：

```text
/drone_0/fmu/in/offboard_control_mode
/drone_0/fmu/in/trajectory_setpoint
/drone_0/fmu/in/vehicle_command
/drone_0/fmu/out/vehicle_status
/drone_0/fmu/out/vehicle_local_position
```

如果看到的是 `/fmu/out/...` 而不是 `/drone_0/fmu/out/...`，说明 PX4 bridge 的命名空间和本工程节点不一致，需要调整节点参数 `namespace`。

## 4. 让无人机起飞

在第三个终端持续发布一个 2 米高度的位置目标：

```bash
ros2 topic pub --rate 10 /drone_0/cmd_pose geometry_msgs/PoseStamped \
"{header: {frame_id: 'world'}, pose: {position: {x: 0.0, y: 0.0, z: 2.0}, orientation: {w: 1.0}}}"
```

注意：

- 这个命令要持续运行，不要只发一次。
- PX4 Offboard 模式要求持续收到 setpoint。
- 本工程对外使用 ROS 常见的 z-up 坐标，`z: 2.0` 表示向上 2 米。
- `px4_offboard` 节点会自动发送 arm 和 Offboard 模式切换命令。

## 5. 查看飞行状态

### 5.1 查看标准 ROS2 位姿

```bash
ros2 topic echo /drone_0/pose
```

正常起飞后，`pose.position.z` 应该逐渐接近 `2.0`。

### 5.2 查看 PX4 飞行状态

```bash
ros2 topic echo /drone_0/fmu/out/vehicle_status
```

重点关注：

| 字段 | 说明 |
|------|------|
| `arming_state` | 是否已解锁 |
| `nav_state` | 当前飞行模式 |

常见状态值：

| 字段 | 值 | 含义 |
|------|----|------|
| `arming_state` | `1` | 已解锁 |
| `nav_state` | `7` | Offboard 模式 |

### 5.3 查看 PX4 本地位置

```bash
ros2 topic echo /drone_0/fmu/out/vehicle_local_position
```

PX4 原始坐标是 NED 坐标系，`z` 向下为正。因此 PX4 原始高度上升时，`z` 通常是负数。本工程发布到 `/drone_0/pose` 时已经转换为 z-up。

## 6. 控制无人机移动

### 6.1 飞到指定位置

例如飞到 `x=1.0, y=1.0, z=2.0`：

```bash
ros2 topic pub --rate 10 /drone_0/cmd_pose geometry_msgs/PoseStamped \
"{header: {frame_id: 'world'}, pose: {position: {x: 1.0, y: 1.0, z: 2.0}, orientation: {w: 1.0}}}"
```

### 6.2 速度控制

例如以 `0.5 m/s` 向 x 方向移动：

```bash
ros2 topic pub --rate 10 /drone_0/cmd_vel geometry_msgs/Twist \
"{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {z: 0.0}}"
```

当前 `px4_offboard` 默认使用位置控制模式。如果要稳定使用纯速度控制，需要进一步把 `OffboardControlMode.velocity` 打开，并把 `position` 设为无效值。

## 7. 降落和停止

### 7.1 降到接近地面

持续发布较低高度：

```bash
ros2 topic pub --rate 10 /drone_0/cmd_pose geometry_msgs/PoseStamped \
"{header: {frame_id: 'world'}, pose: {position: {x: 0.0, y: 0.0, z: 0.2}, orientation: {w: 1.0}}}"
```

### 7.2 停止仿真

依次按 `Ctrl+C` 停止：

1. 发布 `/drone_0/cmd_pose` 的终端
2. ROS2 launch 终端
3. PX4 SITL 终端

`px4_offboard` 节点退出时会发送 disarm 命令。

## 8. 常见问题排查

### 8.1 Gazebo 中有飞机，但是 ROS2 没有 fmu 话题

检查是否 source 了环境：

```bash
source /opt/ros/humble/setup.bash
source ~/FlyControl/ros2_fc/install/setup.bash
ros2 topic list | grep fmu
```

如果仍然没有，检查 PX4 bridge 是否启动、PX4 SITL 终端是否有报错。

### 8.2 有 `/fmu/out/...`，但是没有 `/drone_0/fmu/out/...`

这是命名空间不一致。当前 ROS2 节点默认使用：

```text
/drone_0
```

需要让 PX4 bridge 使用同样命名空间，或者把本工程节点参数 `namespace` 改为空字符串。

### 8.3 飞机不起飞

按顺序检查：

```bash
ros2 topic list | grep fmu
ros2 topic echo /drone_0/fmu/out/vehicle_status
ros2 topic echo /drone_0/fmu/out/vehicle_local_position
ros2 node list
```

确认：

- `px4_offboard_controller` 节点存在
- `/drone_0/cmd_pose` 正在以固定频率发布
- `nav_state` 最终变成 `7`
- `arming_state` 最终变成 `1`

### 8.4 `colcon build --symlink-install` 报 symlink 冲突

如果出现类似错误：

```text
failed to create symbolic link ... existing path cannot be removed: Is a directory
```

通常是旧的 build/install 生成物和 symlink-install 冲突。可以清理对应包后重新编译：

```bash
cd ~/FlyControl/ros2_fc
rm -rf build/px4_msgs install/px4_msgs
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

### 8.5 Gazebo 版本检查返回非 0

如果 `gazebo --version` 能打印版本，但提示打不开日志文件，检查 Gazebo 日志目录权限：

```bash
ls -ld ~/.gazebo
ls -l ~/.gazebo
```

正常目录需要有执行权限，例如：

```text
drwxr-xr-x
```

## 9. 推荐操作顺序

日常测试建议按下面顺序执行：

```bash
# 终端1
cd ~/development/PX4-Autopilot
make px4_sitl gazebo
```

```bash
# 终端2
cd ~/FlyControl/ros2_fc
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch drone_control px4_gazebo.py
```

```bash
# 终端3
cd ~/FlyControl/ros2_fc
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic pub --rate 10 /drone_0/cmd_pose geometry_msgs/PoseStamped \
"{header: {frame_id: 'world'}, pose: {position: {x: 0.0, y: 0.0, z: 2.0}, orientation: {w: 1.0}}}"
```

```bash
# 终端4，可选
cd ~/FlyControl/ros2_fc
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 topic echo /drone_0/pose
```
