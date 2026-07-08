#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/ros/humble/setup.bash
set -u

ros2 topic pub -r 10 --qos-profile sensor_data /scan sensor_msgs/msg/LaserScan "{
  header: {frame_id: 'laser_link'},
  angle_min: -1.5708,
  angle_max: 1.5708,
  angle_increment: 0.3927,
  time_increment: 0.0,
  scan_time: 0.1,
  range_min: 0.1,
  range_max: 10.0,
  ranges: [3.2, 2.8, 2.4, 2.1, 2.0, 2.1, 2.4, 2.8, 3.2],
  intensities: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
}"
