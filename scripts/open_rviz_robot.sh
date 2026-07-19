#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URDF_FILE="${PROJECT_DIR}/urdf/custom_robot_gazebo_preview.urdf"
RVIZ_FILE="${PROJECT_DIR}/config/inspection_robot.rviz"

set +u
source /opt/ros/humble/setup.bash
set -u

cleanup() {
  if [[ -n "${RSP_PID:-}" ]]; then kill "${RSP_PID}" 2>/dev/null || true; fi
  if [[ -n "${TF_PID:-}" ]]; then kill "${TF_PID}" 2>/dev/null || true; fi
  if [[ -n "${PARAM_FILE:-}" ]]; then rm -f "${PARAM_FILE}" 2>/dev/null || true; fi
}
trap cleanup EXIT

PARAM_FILE="$(mktemp)"
{
  echo "/**:"
  echo "  ros__parameters:"
  echo "    robot_description: |"
  sed 's/^/      /' "${URDF_FILE}"
} > "${PARAM_FILE}"

ros2 run robot_state_publisher robot_state_publisher \
  --ros-args --params-file "${PARAM_FILE}" &
RSP_PID=$!

ros2 run tf2_ros static_transform_publisher \
  --x 0 --y 0 --z 0 --roll 3.14159 --pitch 0 --yaw 0 \
  --frame-id odom --child-frame-id base_link &
TF_PID=$!

sleep 1
rviz2 -d "${RVIZ_FILE}"
