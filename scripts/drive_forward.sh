#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/ros/humble/setup.bash
set -u

# Must match open_subway_tunnel.sh so the publisher and Gazebo discover each
# other reliably inside WSL.
export ROS_DOMAIN_ID="${SUBWAY_ROS_DOMAIN_ID:-0}"
export ROS_LOCALHOST_ONLY=1

DURATION="${1:-3}"
SPEED="${2:-0.25}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/drive_forward.py" "${DURATION}" "${SPEED}"
