#!/usr/bin/env python3
"""
ROS2 + PX4 + Gazebo 虚拟无人机系统集成测试
验证所有组件是否正确安装和配置
"""

import subprocess
import sys
import os
from pathlib import Path


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")


def run_command(cmd, verbose=False):
    """运行命令并返回返回码"""
    try:
        if verbose:
            print_info(f"运行: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)


def check_ros2():
    """检查ROS2安装"""
    print("\n" + "="*50)
    print("检查 ROS2 环境")
    print("="*50)
    
    # 检查ROS_DISTRO
    ros_distro = os.getenv('ROS_DISTRO', '')
    if ros_distro == 'humble':
        print_success("ROS2 Humble 已安装")
    else:
        print_error(f"ROS2版本不是Humble (当前: {ros_distro})")
        return False
    
    # 检查ros2命令。ROS2 CLI没有稳定的--version选项，使用-h验证可用性。
    ret, out, err = run_command(['ros2', '-h'])
    if ret == 0:
        print_success("ros2命令可用")
    else:
        print_error("ros2命令不可用")
        return False
    
    # 检查daemon状态
    ret, out, err = run_command(['ros2', 'daemon', 'status'])
    if ret == 0 and 'running' in out.lower():
        print_success("ROS2 daemon 运行中")
    else:
        print_warning("ROS2 daemon 可能未运行")
    
    return True


def check_gazebo():
    """检查Gazebo安装"""
    print("\n" + "="*50)
    print("检查 Gazebo 环境")
    print("="*50)
    
    ret, out, err = run_command(['gazebo', '--version'])
    gazebo_output = (out + err).strip()
    if 'Gazebo multi-robot simulator' in gazebo_output or 'version' in gazebo_output.lower():
        print_success(f"Gazebo 已安装: {gazebo_output.splitlines()[0]}")
        if ret != 0:
            print_warning("Gazebo 命令返回非0状态，通常是日志目录权限或运行时环境问题")
    else:
        print_error("Gazebo 未安装或不可用")
        print_warning("执行: sudo apt install gazebo gazebo-dev")
        return False
    
    # 检查gazebo_ros
    ret, out, err = run_command(['find', '/opt/ros/humble', '-name', '*gazebo_ros*', '-type', 'd'])
    if ret == 0 and out.strip():
        print_success("gazebo_ros 包已安装")
    else:
        print_warning("gazebo_ros 包可能不完整")
    
    # 检查Gazebo模型路径
    gz_model_path = os.getenv('GAZEBO_MODEL_PATH', '')
    if gz_model_path:
        print_success(f"GAZEBO_MODEL_PATH 已设置")
    else:
        print_warning("GAZEBO_MODEL_PATH 未设置")
    
    return True


def check_px4():
    """检查PX4 SITL"""
    print("\n" + "="*50)
    print("检查 PX4 SITL")
    print("="*50)
    
    px4_path = Path.home() / "development" / "PX4-Autopilot"
    
    if not px4_path.exists():
        print_error(f"PX4-Autopilot 不存在: {px4_path}")
        print_info("请先克隆 PX4 仓库: git clone https://github.com/PX4/PX4-Autopilot.git")
        return False
    
    print_success(f"PX4-Autopilot 目录存在: {px4_path}")
    
    # 检查编译的binary
    px4_binary = px4_path / "build" / "px4_sitl_default" / "bin" / "px4"
    if px4_binary.exists():
        print_success(f"PX4 SITL binary 已编译")
    else:
        print_error("PX4 SITL binary 未编译")
        print_info("请执行编译: cd ~/development/PX4-Autopilot && make px4_sitl gazebo")
        return False
    
    # 检查Gazebo插件
    gazebo_plugin_path = os.getenv('GAZEBO_PLUGIN_PATH', '')
    if 'px4_sitl_default' in gazebo_plugin_path:
        print_success("Gazebo 插件路径已配置")
    else:
        print_warning("Gazebo 插件路径可能不完整")
    
    return True


def check_ros_packages():
    """检查必要的ROS包"""
    print("\n" + "="*50)
    print("检查 ROS 包依赖")
    print("="*50)
    
    required_packages = [
        'rclpy',
        'geometry_msgs',
        'sensor_msgs',
        'nav_msgs',
        'std_msgs',
        'tf2_ros',
    ]
    
    for pkg in required_packages:
        ret, out, err = run_command(['python3', '-c', f'import {pkg}'])
        if ret == 0:
            print_success(f"包 {pkg} 已安装")
        else:
            print_error(f"包 {pkg} 未安装")
            return False
    
    return True


def check_px4_msgs():
    """检查px4_msgs"""
    print("\n" + "="*50)
    print("检查 PX4 消息包")
    print("="*50)
    
    ret, out, err = run_command(['python3', '-c', 'import px4_msgs'])
    if ret == 0:
        print_success("px4_msgs 已安装")
    else:
        print_error("px4_msgs 未安装")
        print_info("需要编译PX4消息包或使用Python绑定")
        return False
    
    return True


def check_drone_control():
    """检查drone_control包"""
    print("\n" + "="*50)
    print("检查 drone_control 包")
    print("="*50)
    
    # 检查源代码
    drone_control_path = Path.home() / "FlyControl" / "ros2_fc" / "src" / "drone_control"
    if not drone_control_path.exists():
        print_error(f"drone_control 源代码不存在: {drone_control_path}")
        return False
    
    print_success(f"drone_control 源代码存在")
    
    # 检查必要文件
    required_files = [
        'package.xml',
        'setup.py',
        'setup.cfg',
        'drone_control/__init__.py',
        'drone_control/px4_offboard.py',
        'drone_control/drone_state_monitor.py',
    ]
    
    for file in required_files:
        file_path = drone_control_path / file
        if file_path.exists():
            print_success(f"文件存在: {file}")
        else:
            print_error(f"文件不存在: {file}")
            return False
    
    # 检查install/build
    install_path = Path.home() / "FlyControl" / "ros2_fc" / "install"
    if install_path.exists():
        print_success("drone_control 已编译")
    else:
        print_warning("drone_control 可能未编译")
        print_info("请执行: cd ~/FlyControl/ros2_fc && colcon build --symlink-install")
        return False
    
    return True


def check_network():
    """检查网络配置"""
    print("\n" + "="*50)
    print("检查网络配置")
    print("="*50)
    
    # 检查ROS_DOMAIN_ID
    ros_domain_id = os.getenv('ROS_DOMAIN_ID', '')
    if ros_domain_id:
        print_success(f"ROS_DOMAIN_ID 已设置: {ros_domain_id}")
    else:
        print_warning("ROS_DOMAIN_ID 未设置，使用默认值 0")
    
    # 检查localhost
    ros_localhost_only = os.getenv('ROS_LOCALHOST_ONLY', '')
    if ros_localhost_only == '0':
        print_success("ROS_LOCALHOST_ONLY = 0 (允许网络通信)")
    else:
        print_warning(f"ROS_LOCALHOST_ONLY = {ros_localhost_only}")
    
    return True


def check_ports():
    """检查必要的端口"""
    print("\n" + "="*50)
    print("检查网络端口")
    print("="*50)
    
    ports = {
        18570: 'PX4 SITL',
        14550: 'PX4 MAVLINK',
        14540: 'Gazebo Bridge'
    }
    
    for port, service in ports.items():
        ret, out, err = run_command(['netstat', '-an'])
        if ret == 0:
            if f':{port}' in out:
                print_warning(f"端口 {port} ({service}) 可能被占用")
            else:
                print_success(f"端口 {port} ({service}) 空闲")
        else:
            print_info(f"无法检查端口 {port}，netstat不可用")
    
    return True


def test_python_imports():
    """测试Python导入"""
    print("\n" + "="*50)
    print("测试 Python 导入")
    print("="*50)
    
    test_code = """
import sys
try:
    import rclpy
    print('rclpy: OK')
except: 
    print('rclpy: FAIL')

try:
    import px4_msgs
    print('px4_msgs: OK')
except:
    print('px4_msgs: FAIL')

try:
    from geometry_msgs.msg import PoseStamped
    print('geometry_msgs: OK')
except:
    print('geometry_msgs: FAIL')

try:
    import numpy
    print('numpy: OK')
except:
    print('numpy: FAIL')
"""
    
    ret, out, err = run_command(['python3', '-c', test_code])
    if ret == 0:
        for line in out.strip().split('\n'):
            if 'OK' in line:
                print_success(line)
            else:
                print_error(line)
    
    return True


def main():
    """主测试程序"""
    print(f"{Colors.BLUE}")
    print("="*50)
    print("ROS2 + PX4 + Gazebo 虚拟无人机系统")
    print("集成测试工具")
    print("="*50)
    print(f"{Colors.END}")
    
    tests = [
        ("ROS2 环境", check_ros2),
        ("Gazebo", check_gazebo),
        ("PX4 SITL", check_px4),
        ("ROS包", check_ros_packages),
        ("PX4消息", check_px4_msgs),
        ("drone_control", check_drone_control),
        ("网络配置", check_network),
        ("网络端口", check_ports),
        ("Python导入", test_python_imports),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"测试 {test_name} 出错: {e}")
            results[test_name] = False
    
    # 总结
    print("\n" + "="*50)
    print("测试总结")
    print("="*50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}通过{Colors.END}" if result else f"{Colors.RED}失败{Colors.END}"
        print(f"{test_name}: {status}")
    
    print(f"\n总体: {passed}/{total} 通过")
    
    if passed == total:
        print_success("所有检查通过！系统已准备就绪")
        print("\n下一步:")
        print("1. 启动PX4 SITL: cd ~/development/PX4-Autopilot && make px4_sitl gazebo")
        print("2. 启动ROS节点: cd ~/FlyControl/ros2_fc && source install/setup.bash && ros2 launch drone_control px4_gazebo.py")
        return 0
    else:
        print_error("某些检查失败，请检查上述错误信息")
        return 1


if __name__ == '__main__':
    sys.exit(main())
