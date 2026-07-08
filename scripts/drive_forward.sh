#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/ros/humble/setup.bash
set -u

DURATION="${1:-8}"
SPEED="${2:-0.8}"

# 修改前：ros2 topic pub --once /cmd_vel ... 只发一次速度命令。
# 修改后：持续发布速度命令，比 --once 更容易在 Gazebo 里观察模型平移。
timeout "${DURATION}" ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: ${SPEED}, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" || true

# 修改前：没有主动停车命令。
# 修改后：测试结束后主动发 0 速度，避免模型继续保持上一次速度。
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
