from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'drone_control'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 安装launch文件
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.py'))),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.xml'))),
        # 安装config文件
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*'))),
        # 安装worlds文件
        (os.path.join('share', package_name, 'worlds'), glob(os.path.join('worlds', '*.world'))),
        # 安装models文件
        (os.path.join('share', package_name, 'models'), glob(os.path.join('models', '**', '*'), recursive=True)),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ywt',
    maintainer_email='ywt@todo.todo',
    description='ROS2虚拟无人机控制系统，支持PX4 SITL和Gazebo仿真',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'talker = drone_control.talker:main',
            'px4_offboard = drone_control.px4_offboard:main',
            'drone_state_monitor = drone_control.drone_state_monitor:main',
            'gazebo_sim_interface = drone_control.gazebo_sim_interface:main',
            'trajectory_experiment = drone_control.trajectory_experiment:main',
            'gazebo_trajectory_visualizer = drone_control.gazebo_trajectory_visualizer:main',
        ],
    },
)
