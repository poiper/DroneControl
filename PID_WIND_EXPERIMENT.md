# 有风条件下 PID 轨迹实验

目标：让 PX4 SITL + Gazebo 中的虚拟无人机先稳定起飞，再用固定轨迹对比不同 PX4 位置/速度控制参数在有风条件下的跟踪误差。

## 1. 编译工作区

```bash
cd ~/FlyControl/ros2_fc
colcon build --symlink-install
source install/setup.bash
```

## 2. 启动仿真

推荐先用 PX4 官方命令启动 SITL 和 Gazebo：

```bash
cd ~/development/PX4-Autopilot
make px4_sitl gazebo
```

再启动 ROS2 控制节点：

```bash
cd ~/FlyControl/ros2_fc
source install/setup.bash
ros2 launch drone_control px4_gazebo.py namespace:=/drone_0 takeoff_altitude:=2.0
```

如果 PX4 DDS 话题是 `/fmu/out/...`，而不是 `/drone_0/fmu/out/...`，把 namespace 改为空：

```bash
ros2 launch drone_control px4_gazebo.py namespace:=''
```

启动后 `px4_offboard` 会自动持续发布 2m 悬停目标、arm，并请求 Offboard 模式。检查：

```bash
ros2 topic echo /drone_0/pose
ros2 topic echo /drone_0/fmu/out/vehicle_status
```

## 3. 有风 world

项目新增了 `src/drone_control/worlds/windy_world.world`，其中风速为 x 方向 3 m/s。若用本 launch 启动 Gazebo：

```bash
ros2 launch drone_control px4_gazebo.py \
  start_gazebo:=true \
  world:=$HOME/FlyControl/ros2_fc/src/drone_control/worlds/windy_world.world
```

注意：如果用 `make px4_sitl gazebo` 启动 Gazebo，则 PX4 会使用自己的默认 world。要做风场实验，需要把 PX4 启动使用的 world 换成带风版本，或在 Gazebo/PX4 仿真模型中启用对应风插件。

## 4. 运行固定轨迹并记录 CSV

悬停：

```bash
ros2 run drone_control trajectory_experiment --ros-args \
  -p namespace:=/drone_0 \
  -p pattern:=hover \
  -p duration:=60.0
```

圆轨迹：

```bash
ros2 run drone_control trajectory_experiment --ros-args \
  -p namespace:=/drone_0 \
  -p pattern:=circle \
  -p radius:=2.0 \
  -p speed:=0.6 \
  -p altitude:=2.0 \
  -p duration:=90.0
```

支持的 `pattern`：`hover`、`line`、`circle`、`figure8`。CSV 默认写到 `/tmp/drone_trajectory_<pattern>_<timestamp>.csv`，字段包括目标位置、实际位置和三维误差。

## 5. 调不同 PID 参数

PX4 多旋翼位置控制常用参数：

```text
MPC_XY_P            水平位置 P
MPC_Z_P             高度位置 P
MPC_XY_VEL_P_ACC    水平速度环 P
MPC_XY_VEL_I_ACC    水平速度环 I
MPC_XY_VEL_D_ACC    水平速度环 D
MPC_Z_VEL_P_ACC     垂直速度环 P
MPC_Z_VEL_I_ACC     垂直速度环 I
MPC_Z_VEL_D_ACC     垂直速度环 D
```

在 PX4 shell 中先记录基线：

```bash
param show MPC_XY_P
param show MPC_XY_VEL_P_ACC
param show MPC_XY_VEL_I_ACC
param show MPC_XY_VEL_D_ACC
```

每次只改一组参数，然后跑同一条轨迹：

```bash
param set MPC_XY_P 1.0
param set MPC_XY_VEL_P_ACC 3.0
param set MPC_XY_VEL_I_ACC 1.0
param set MPC_XY_VEL_D_ACC 0.1
```

实验记录建议固定格式：

```text
wind_x=3.0, pattern=circle, radius=2.0, speed=0.6
pid_set=A, MPC_XY_P=..., MPC_XY_VEL_P_ACC=..., MPC_XY_VEL_I_ACC=..., MPC_XY_VEL_D_ACC=...
csv=/tmp/drone_trajectory_circle_YYYYMMDD_HHMMSS.csv
```

比较指标：平均误差、最大误差、稳态偏差、超调量、回到轨迹所需时间。

## 6. 一键实验脚本

项目提供两个一键脚本：

```bash
cd ~/FlyControl/ros2_fc

# 无风实验，默认读取 config/no_wind_pid_test.json
./scripts/run_no_wind_pid_test.sh

# 有风实验，默认读取 config/wind_pid_test.json
./scripts/run_wind_pid_test.sh
```

也可以传入自定义 JSON：

```bash
./scripts/run_wind_pid_test.sh ~/my_wind_pid_config.json
```

脚本会自动启动三组进程：

```text
MicroXRCEAgent
PX4 SITL + Gazebo
ROS2 offboard + trajectory_experiment
```

按 `Ctrl+C` 会统一停止这些进程。

JSON 中主要字段：

```json
{
  "simulation": {
    "world": "windy"
  },
  "pid": {
    "MPC_XY_P": 0.95,
    "MPC_XY_VEL_P_ACC": 1.8,
    "MPC_XY_VEL_I_ACC": 0.4,
    "MPC_XY_VEL_D_ACC": 0.2
  },
  "trajectory": {
    "pattern": "circle",
    "radius": 2.0,
    "speed": 0.6,
    "altitude": 2.0,
    "duration": 60.0
  }
}
```

每次运行会创建一个结果目录：

```text
results/<prefix>_<timestamp>/
```

里面包含：

```text
*_trajectory.csv   轨迹目标、实际位置和误差
*_pid.json         本次设置的 PID 参数
*_config.json      本次完整配置
agent.log          MicroXRCEAgent 日志
px4_gazebo.log     PX4/Gazebo 日志
ros_launch.log     ROS2 控制日志
trajectory.log     轨迹实验节点日志
```

## 7. Gazebo 中显示轨迹

`px4_gazebo.py` 支持在 Gazebo 中显示目标轨迹和实际轨迹：

```bash
ros2 launch drone_control px4_gazebo.py \
  namespace:=/drone_0 \
  takeoff_altitude:=2.0 \
  start_trajectory_visualizer:=true
```

显示规则：

```text
蓝色小球：/drone_0/cmd_pose 目标轨迹
红色小球：/drone_0/pose 实际飞行轨迹
```

一键实验脚本默认会开启这个可视化。要关闭，在 JSON 中设置：

```json
"visualization": {
  "gazebo_trajectory": false
}
```

也可以单独运行可视化节点：

```bash
ros2 run drone_control gazebo_trajectory_visualizer --ros-args \
  -p namespace:=/drone_0
```

这个节点通过 Gazebo 的 `/spawn_entity` 服务放置轨迹点，所以 PX4/Gazebo 必须由带 `libgazebo_ros_factory.so` 的方式启动。当前 `make px4_sitl gazebo` 已包含该插件。
