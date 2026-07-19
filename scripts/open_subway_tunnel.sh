#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

set +u
source /opt/ros/humble/setup.bash
set -u

# Gazebo and the test command run in the same WSL instance.  Restrict DDS to
# loopback so /cmd_vel discovery does not select an unusable WSL interface.
export ROS_DOMAIN_ID="${SUBWAY_ROS_DOMAIN_ID:-0}"
export ROS_LOCALHOST_ONLY=1
export GAZEBO_MODEL_PATH="${PROJECT_DIR}/models:${GAZEBO_MODEL_PATH:-}"
export GAZEBO_PLUGIN_PATH="/opt/ros/humble/lib:${GAZEBO_PLUGIN_PATH:-}"

# Some non-interactive WSL terminals do not inherit WSLg variables even
# though the display sockets are available.  Fill in only missing values.
if [[ -z "${DISPLAY:-}" && -S /tmp/.X11-unix/X0 ]]; then
  export DISPLAY=:0
fi
if [[ -z "${PULSE_SERVER:-}" && -S /mnt/wslg/PulseServer ]]; then
  export PULSE_SERVER=unix:/mnt/wslg/PulseServer
fi

exec gazebo "${PROJECT_DIR}/worlds/subway_track_tunnel.world"
