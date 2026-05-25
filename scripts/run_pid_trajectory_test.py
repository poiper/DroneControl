#!/usr/bin/env python3
"""
Run a complete PX4 SITL, Gazebo, ROS2 offboard, and trajectory experiment.
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path


class ManagedProcess:
    def __init__(self, name, cmd, env, cwd, log_path, stdin=False, ready_patterns=None):
        self.name = name
        self.cmd = cmd
        self.env = env
        self.cwd = cwd
        self.log_path = log_path
        self.ready_patterns = ready_patterns or []
        self.ready = threading.Event()
        self.process = None
        self.thread = None
        self._log_file = None
        self._stdin = subprocess.PIPE if stdin else None

    def start(self):
        self._log_file = open(self.log_path, "w", encoding="utf-8", buffering=1)
        self.process = subprocess.Popen(
            self.cmd,
            cwd=self.cwd,
            env=self.env,
            stdin=self._stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            preexec_fn=os.setsid,
        )
        self.thread = threading.Thread(target=self._read_output, daemon=True)
        self.thread.start()
        print(f"[{self.name}] started pid={self.process.pid}, log={self.log_path}")

    def _read_output(self):
        assert self.process is not None
        for line in self.process.stdout:
            self._log_file.write(line)
            line = line.rstrip()
            if line:
                print(f"[{self.name}] {line}")
            for pattern in self.ready_patterns:
                if pattern in line:
                    self.ready.set()

    def write(self, text):
        if self.process is None or self.process.stdin is None:
            return
        self.process.stdin.write(text)
        self.process.stdin.flush()

    def poll(self):
        return None if self.process is None else self.process.poll()

    def stop(self, timeout=8):
        if self.process is None or self.process.poll() is not None:
            return
        print(f"[{self.name}] stopping pid={self.process.pid}")
        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
        finally:
            if self._log_file:
                self._log_file.close()


def expand_path(value):
    return str(Path(value).expanduser())


def load_config(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def ros_env(config):
    env = os.environ.copy()
    ros = config["ros"]
    env["ROS_DOMAIN_ID"] = str(ros.get("domain_id", 0))
    env["ROS_LOCALHOST_ONLY"] = str(ros.get("localhost_only", 0))
    env["RMW_IMPLEMENTATION"] = ros.get("rmw_implementation", "rmw_fastrtps_cpp")
    return env


def bash_cmd(command):
    return ["bash", "-lc", command]


def wait_for_dds(config, timeout_s):
    workspace = expand_path(config["workspace"])
    namespace = config["ros"].get("namespace", "/drone_0").rstrip("/")
    topic = f"{namespace}/fmu/out/vehicle_status"
    command = (
        f"source /opt/ros/humble/setup.bash && "
        f"source {workspace}/install/setup.bash && "
        f"ros2 topic info --no-daemon -v {topic}"
    )
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        result = subprocess.run(
            bash_cmd(command),
            cwd=workspace,
            env=ros_env(config),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if "Publisher count: 1" in result.stdout:
            print(f"[dds] PX4 publisher found on {topic}")
            return True
        time.sleep(1.0)
    print(f"[dds] PX4 publisher not found on {topic}")
    print(result.stdout)
    return False


def apply_pid_params(px4_process, params):
    if not params:
        return
    print("[px4] applying PID parameters")
    for name, value in params.items():
        px4_process.write(f"param set {name} {value}\n")
        time.sleep(0.15)
    px4_process.write("param save\n")


def copy_config(config_path, output_dir, run_name):
    target = output_dir / f"{run_name}_config.json"
    shutil.copyfile(config_path, target)
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Experiment JSON config")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    config = load_config(config_path)
    workspace = Path(expand_path(config["workspace"]))
    px4_dir = Path(expand_path(config["px4_dir"]))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_cfg = config.get("output", {})
    prefix = output_cfg.get("prefix", config.get("name", "pid_test"))
    run_name = f"{prefix}_{stamp}"
    output_dir = Path(expand_path(output_cfg.get("directory", str(workspace / "results")))) / run_name
    output_dir.mkdir(parents=True, exist_ok=True)
    copied_config = copy_config(config_path, output_dir, run_name)

    env = ros_env(config)
    namespace = config["ros"].get("namespace", "/drone_0")
    takeoff_altitude = float(config["ros"].get("takeoff_altitude", 2.0))
    world = config.get("simulation", {}).get("world", "empty")
    model = config.get("simulation", {}).get("model", "gazebo")
    timeouts = config.get("timeouts", {})
    gazebo_trajectory = str(
        bool(config.get("visualization", {}).get("gazebo_trajectory", True))
    ).lower()

    trajectory = config["trajectory"]
    trajectory_csv = output_dir / f"{run_name}_trajectory.csv"
    pid_json = output_dir / f"{run_name}_pid.json"
    with open(pid_json, "w", encoding="utf-8") as handle:
        json.dump(config.get("pid", {}), handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"[run] config={copied_config}")
    print(f"[run] pid={pid_json}")
    print(f"[run] trajectory={trajectory_csv}")

    agent = ManagedProcess(
        "agent",
        [
            config["agent"].get("command", "/usr/local/bin/MicroXRCEAgent"),
            "udp4",
            "-p",
            str(config["agent"].get("port", 8888)),
            "-v",
            str(config["agent"].get("verbose", 4)),
        ],
        env,
        str(workspace),
        str(output_dir / "agent.log"),
        ready_patterns=["running", "UDP"],
    )

    world_env = "" if world in ("", "empty", None) else f"PX4_SITL_WORLD={world} "
    px4_cmd = (
        f"source /opt/ros/humble/setup.bash && "
        f"cd {px4_dir} && "
        f"PX4_UXRCE_DDS_NS={namespace.strip('/')} {world_env}make px4_sitl {model}"
    )
    px4 = ManagedProcess(
        "px4",
        bash_cmd(px4_cmd),
        env,
        str(px4_dir),
        str(output_dir / "px4_gazebo.log"),
        stdin=True,
        ready_patterns=["Ready for takeoff!"],
    )

    ros_launch_cmd = (
        f"source /opt/ros/humble/setup.bash && "
        f"source {workspace}/install/setup.bash && "
        f"ros2 launch drone_control px4_gazebo.py "
        f"namespace:={namespace} takeoff_altitude:={takeoff_altitude} "
        f"start_trajectory_visualizer:={gazebo_trajectory}"
    )
    ros_launch = ManagedProcess(
        "ros",
        bash_cmd(ros_launch_cmd),
        env,
        str(workspace),
        str(output_dir / "ros_launch.log"),
    )

    traj_cmd = (
        f"source /opt/ros/humble/setup.bash && "
        f"source {workspace}/install/setup.bash && "
        f"ros2 run drone_control trajectory_experiment --ros-args "
        f"-p namespace:={namespace} "
        f"-p pattern:={trajectory.get('pattern', 'circle')} "
        f"-p radius:={trajectory.get('radius', 2.0)} "
        f"-p speed:={trajectory.get('speed', 0.6)} "
        f"-p altitude:={trajectory.get('altitude', takeoff_altitude)} "
        f"-p duration:={trajectory.get('duration', 60.0)} "
        f"-p publish_rate:={trajectory.get('publish_rate', 20.0)} "
        f"-p output_file:={trajectory_csv}"
    )
    trajectory_process = ManagedProcess(
        "trajectory",
        bash_cmd(traj_cmd),
        env,
        str(workspace),
        str(output_dir / "trajectory.log"),
    )

    processes = [agent, px4, ros_launch, trajectory_process]
    try:
        agent.start()
        time.sleep(1.0)
        px4.start()
        if not px4.ready.wait(float(timeouts.get("px4_ready_s", 90))):
            raise RuntimeError("PX4 did not report Ready for takeoff before timeout")

        apply_pid_params(px4, config.get("pid", {}))
        if not wait_for_dds(config, float(timeouts.get("dds_ready_s", 30))):
            raise RuntimeError("PX4 DDS publisher not visible in ROS2")

        ros_launch.start()
        time.sleep(float(timeouts.get("hover_settle_s", 8)))
        trajectory_process.start()

        while trajectory_process.poll() is None:
            time.sleep(0.5)
        print(f"[run] trajectory process exited with code {trajectory_process.poll()}")
        print(f"[run] results directory: {output_dir}")
    except KeyboardInterrupt:
        print("\n[run] interrupted; stopping all processes")
    except Exception as exc:
        print(f"[run] failed: {exc}", file=sys.stderr)
        return 1
    finally:
        for process in reversed(processes):
            process.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
