#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

set +u
source /opt/ros/humble/setup.bash
set -u

export GAZEBO_MODEL_PATH="${PROJECT_DIR}/models:${GAZEBO_MODEL_PATH:-}"
export GAZEBO_PLUGIN_PATH="/opt/ros/humble/lib:${GAZEBO_PLUGIN_PATH:-}"

exec gazebo "${PROJECT_DIR}/worlds/custom_robot_tunnel.world"
