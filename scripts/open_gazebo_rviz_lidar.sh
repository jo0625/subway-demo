#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORLD_FILE="${PROJECT_DIR}/worlds/subway_track_tunnel.world"
URDF_FILE="${PROJECT_DIR}/urdf/gazebo_train_tf.urdf"
RVIZ_FILE="${PROJECT_DIR}/config/gazebo_lidar.rviz"

set +u
source /opt/ros/humble/setup.bash
set -u

export GAZEBO_MODEL_PATH="${PROJECT_DIR}/models:${GAZEBO_MODEL_PATH:-}"
export GAZEBO_PLUGIN_PATH="/opt/ros/humble/lib:${GAZEBO_PLUGIN_PATH:-}"

cleanup() {
  if [[ -n "${GAZEBO_PID:-}" ]]; then kill "${GAZEBO_PID}" 2>/dev/null || true; fi
  if [[ -n "${RSP_PID:-}" ]]; then kill "${RSP_PID}" 2>/dev/null || true; fi
}
trap cleanup EXIT

gazebo "${WORLD_FILE}" &
GAZEBO_PID=$!

ros2 run robot_state_publisher robot_state_publisher \
  --ros-args -p "robot_description:=$(tr '\n' ' ' < "${URDF_FILE}")" &
RSP_PID=$!

sleep 3
rviz2 -d "${RVIZ_FILE}"
