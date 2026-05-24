# 虚拟无人机系统安装与配置指南

## 完整安装步骤

### 第一步：系统环境准备

#### 1.1 验证基础环境

```bash
# 检查Ubuntu版本（必须是22.04）
lsb_release -a

# 检查ROS2 Humble
printenv ROS_DISTRO
# 如果输出不是 humble，需要安装ROS2

# 检查Python版本（必须≥3.10）
python3 --version

# 检查Gazebo（可选，某些情况下ROS2已包含）
gazebo --version
```

#### 1.2 安装ROS2 Humble（如需要）

```bash
# 设置ROS2密钥
sudo apt update && sudo apt install curl gnupg lsb-release ubuntu-keyring
curl -sSL https://repo.ros2.org/ros.key | sudo apt-key add -

# 添加ROS2仓库
sudo sh -c 'echo "deb [arch=$(dpkg --print-architecture)] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'

# 安装ROS2
sudo apt update
sudo apt install -y ros-humble-desktop

# 设置环境
source /opt/ros/humble/setup.bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

### 第二步：安装仿真环境

#### 2.1 安装Gazebo相关包

```bash
# 安装Gazebo和ROS2集成包
sudo apt install -y \
    gazebo \
    gazebo-dev \
    ros-humble-gazebo-msgs \
    ros-humble-gazebo-plugins \
    ros-humble-gazebo-ros \
    ros-humble-gazebo-ros2-control \
    ros-humble-gazebo-ros-pkgs
```

#### 2.2 安装控制相关包

```bash
sudo apt install -y \
    ros-humble-control-toolbox \
    ros-humble-controller-manager \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-joint-state-publisher \
    ros-humble-robot-state-publisher
```

#### 2.3 安装通用消息和工具

```bash
sudo apt install -y \
    python3-pip \
    python3-colcon-common-extensions \
    ros-humble-tf2 \
    ros-humble-tf2-ros \
    ros-humble-nav2-common
```

### 第三步：安装PX4

#### 3.1 安装系统依赖

```bash
# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装编译工具
sudo apt install -y \
    git \
    build-essential \
    ccache \
    cmake \
    ninja-build \
    pkg-config

# 安装Python依赖
sudo apt install -y \
    python3-jinja2 \
    python3-pyyaml \
    python3-pip

pip3 install \
    pycurl \
    future \
    numpy \
    pyserial \
    empy \
    toml \
    opencv-python
```

#### 3.2 下载并编译PX4

```bash
# 创建工作目录
mkdir -p ~/development
cd ~/development

# 克隆PX4仓库（v1.14.x版本）
git clone https://github.com/PX4/PX4-Autopilot.git --depth 1 -b v1.14.0
cd PX4-Autopilot

# 运行初始化脚本
bash ./Tools/setup/ubuntu.sh

# 注销并重新登录（使新组员生效）
# 或者使用 newgrp 临时更改组
newgrp dialout

# 编译PX4 SITL
make px4_sitl gazebo

# 验证编译成功
ls -la build/px4_sitl_default/bin/px4
```

#### 3.3 配置Gazebo模型路径

```bash
# 添加到 ~/.bashrc
cat >> ~/.bashrc << 'EOF'

# PX4 Gazebo仿真环境配置
export PX4_HOME=$HOME/development/PX4-Autopilot
export PATH=$PX4_HOME/Tools/simulation/gazebo/sitl_gazebo/bin:$PATH
export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:$PX4_HOME/build/px4_sitl_default/build_gazebo
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:$PX4_HOME/Tools/simulation/gazebo/sitl_gazebo/models:$PX4_HOME/models

# ROS2 PX4集成
export ROS_DOMAIN_ID=0
EOF

# 应用配置
source ~/.bashrc
```

### 第四步：配置ROS2项目

#### 4.1 创建工作空间（如需要）

```bash
# 创建工作空间
mkdir -p ~/FlyControl/ros2_fc/src
cd ~/FlyControl/ros2_fc

# 初始化工作空间
colcon build --symlink-install
```

#### 4.2 更新package依赖

```bash
cd ~/FlyControl/ros2_fc/src/drone_control

# 使用rosdep安装依赖
rosdep install -i --from-path . --rosdistro humble -y
```

#### 4.3 编译项目

```bash
cd ~/FlyControl/ros2_fc

# 编译所有包
colcon build --symlink-install

# 如果只编译特定包
colcon build --packages-select drone_control --symlink-install

# 验证编译结果
source install/setup.bash
ros2 run drone_control px4_offboard --help
```

### 第五步：验证安装

#### 5.1 检查所有依赖

```bash
# 检查ROS2环境
ros2 --version

# 检查gazebo
gazebo --version

# 检查PX4
~/development/PX4-Autopilot/build/px4_sitl_default/bin/px4 --help

# 检查Python包
python3 -c "import rclpy, geometry_msgs, px4_msgs; print('All imports OK')"
```

#### 5.2 运行简单测试

```bash
# 测试ROS2通信
ros2 daemon status

# 测试节点列表
ros2 node list

# 测试主题列表（启动后）
ros2 topic list
```

## 快速启动脚本

创建启动脚本 `~/start_simulation.sh`:

```bash
#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== ROS2 + PX4 SITL + Gazebo 仿真启动脚本 ===${NC}"

# 检查环境
echo -e "${YELLOW}[1/5] 检查环境...${NC}"
if [ -z "$ROS_DISTRO" ]; then
    echo "Error: ROS2未安装或未source"
    exit 1
fi

if [ ! -d "$HOME/development/PX4-Autopilot" ]; then
    echo "Error: PX4-Autopilot不存在"
    exit 1
fi

echo -e "${GREEN}✓ 环境检查完成${NC}"

# 设置环境变量
echo -e "${YELLOW}[2/5] 配置环境变量...${NC}"
export PX4_HOME=$HOME/development/PX4-Autopilot
export GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:$PX4_HOME/build/px4_sitl_default/build_gazebo
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:$PX4_HOME/Tools/simulation/gazebo/sitl_gazebo/models
export ROS_DOMAIN_ID=0

echo -e "${GREEN}✓ 环境变量配置完成${NC}"

# 启动Gazebo
echo -e "${YELLOW}[3/5] 启动Gazebo...${NC}"
gazebo --verbose worlds/empty.world &
GAZEBO_PID=$!
sleep 3
echo -e "${GREEN}✓ Gazebo已启动 (PID: $GAZEBO_PID)${NC}"

# 启动PX4 SITL
echo -e "${YELLOW}[4/5] 启动PX4 SITL...${NC}"
cd $PX4_HOME
make px4_sitl_default gazebo_iris &
PX4_PID=$!
sleep 5
echo -e "${GREEN}✓ PX4 SITL已启动 (PID: $PX4_PID)${NC}"

# 启动ROS2节点
echo -e "${YELLOW}[5/5] 启动ROS2节点...${NC}"
cd ~/FlyControl/ros2_fc
source install/setup.bash
ros2 launch drone_control px4_gazebo.py &
ROS_PID=$!

echo -e "${GREEN}✓ ROS2节点已启动 (PID: $ROS_PID)${NC}"

echo -e "${GREEN}=== 仿真环境启动完成 ===${NC}"
echo "运行中的进程:"
echo "  - Gazebo (PID: $GAZEBO_PID)"
echo "  - PX4 SITL (PID: $PX4_PID)"
echo "  - ROS2 (PID: $ROS_PID)"
echo ""
echo "停止仿真，请执行:"
echo "  kill $GAZEBO_PID $PX4_PID $ROS_PID"

# 等待中断信号
trap "kill $GAZEBO_PID $PX4_PID $ROS_PID" SIGINT SIGTERM
wait
```

使用脚本：
```bash
chmod +x ~/start_simulation.sh
~/start_simulation.sh
```

## 故障排除

### 问题1：编译失败 - 找不到gazebo_ros

**错误信息**:
```
Could not find ament_cmake_target_dependencies
```

**解决方案**:
```bash
# 安装缺失的ament包
sudo apt install -y ros-humble-ament-cmake*

# 清理并重新编译
colcon clean all
colcon build --symlink-install
```

### 问题2：PX4启动报错 - No module named 'jinja2'

**错误信息**:
```
ModuleNotFoundError: No module named 'jinja2'
```

**解决方案**:
```bash
pip3 install jinja2 pyyaml
pip3 install --upgrade pip
```

### 问题3：Gazebo启动慢或崩溃

**解决方案**:
```bash
# 清除Gazebo缓存
rm -rf ~/.gazebo

# 重新启动
gazebo --verbose
```

### 问题4：UDP连接失败

**症状**: PX4无法连接到Gazebo

**解决方案**:
```bash
# 检查端口占用
netstat -an | grep 14550
lsof -i :14550

# 检查防火墙
sudo ufw allow 14550/udp

# 手动测试连接
telnet localhost 14550
```

## 下一步

1. **测试Offboard控制**:
   ```bash
   ros2 run drone_control px4_offboard
   ```

2. **发送控制命令**:
   ```bash
   ros2 topic pub /drone_0/cmd_pose geometry_msgs/PoseStamped \
     "{header: {frame_id: 'world'}, pose: {position: {x: 1.0, y: 0.0, z: 2.0}, orientation: {w: 1.0}}}"
   ```

3. **监控状态**:
   ```bash
   ros2 topic echo /drone_0/pose
   ```

## 性能优化建议

```bash
# 使用Release编译以提高性能
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

# 禁用某些Gazebo物理特性以加速
export GAZEBO_REAL_TIME_UPDATE_RATE=100
export GAZEBO_MAX_STEP_SIZE=0.01
```

## 后续支持

- 遇到问题请查阅README.md
- 查看日志: `~/.ros/latest/`
- 检查ROS2文档: https://docs.ros.org/en/humble/
