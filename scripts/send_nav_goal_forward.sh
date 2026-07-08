#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/ros/humble/setup.bash
set -u

DISTANCE="${1:-4.0}"
# 修改前：直接把输入距离当成 odom 目标 x，例如 x=4。
# 修改后：Gazebo world 里机器人出生在 x=-38 附近；这里把“前进距离”换算成 odom 里的绝对目标。
START_X="${START_X:--38.0}"
GOAL_X="$(awk -v start="${START_X}" -v distance="${DISTANCE}" 'BEGIN { printf "%.3f", start + distance }')"

# 修改前：position: {x: ${DISTANCE}, y: 0.0, z: 0.0}
# 修改后：目标点沿隧道 X 方向前进，Y 保持在轨道中心附近。
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{
  pose: {
    header: {frame_id: 'odom'},
    pose: {
      position: {x: ${GOAL_X}, y: -0.018, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    }
  }
}"
