#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ROS_LOG_DIR="${ROS_LOG_DIR:-${PROJECT_DIR}/results/ros_logs}"
mkdir -p "${ROS_LOG_DIR}"

if [[ -f /opt/ros/humble/setup.bash ]]; then
  # shellcheck source=/dev/null
  set +u
  source /opt/ros/humble/setup.bash
  set -u
fi

cd "${PROJECT_DIR}"
python3 vision_demo/vision_node.py "$@"
