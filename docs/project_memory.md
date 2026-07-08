# Project Memory

This file keeps the recovered working context for the subway patrol robot
simulation and competition planning work. It exists so the project can be
resumed even if chat context disappears.

## Current Repository State

- Branch: `feature/simulation`
- Git history: no commits yet on this branch
- Most files are currently untracked, including `config/`, `docs/`, `models/`,
  `scripts/`, `urdf/`, and `worlds/`

## Project Goal

Build a subway patrol robot simulation and supporting competition material for
the metro tunnel multi-domain defect inspection topic.

The competition work is centered on:

- Defect detection and segmentation
- Sensor fusion and localization
- A patrol robot or simulation demo
- A technical report and visualization/reporting workflow

## Key Existing Files

- `worlds/subway_track_tunnel.world`: Gazebo Classic subway tunnel world.
- `models/gazebo_train/model.sdf`: Main simulated robot model with lidar,
  camera, IMU, differential drive, and simplified stable collision geometry.
- `models/custom_robot/model.sdf`: Static Gazebo preview model converted from
  the imported SolidWorks robot, using normalized mesh names under
  `models/custom_robot/meshes/`.
- `urdf/gazebo_train_tf.urdf`: TF/robot_state_publisher URDF for RViz.
- `urdf/custom_robot_gazebo_preview.urdf`: Fixed-joint RViz preview URDF for
  the imported custom robot model.
- `config/nav2_odom_params.yaml`: Nav2 config using `odom` as the global frame.
- `config/gazebo_lidar.rviz`: RViz config for Gazebo, lidar, and Nav2.
- `config/inspection_robot.rviz`: Minimal RViz RobotModel view for checking
  URDF mesh orientation and TF.
- `scripts/open_subway_tunnel.sh`: Opens the Gazebo tunnel world.
- `scripts/open_gazebo_rviz_lidar.sh`: Opens Gazebo, robot_state_publisher,
  and RViz.
- `scripts/open_nav2_demo.sh`: Opens Gazebo, robot_state_publisher, Nav2, and
  RViz.
- `scripts/open_custom_robot_preview.sh`: Opens the static custom robot preview
  world in Gazebo.
- `scripts/open_rviz_robot.sh`: Opens the fixed-joint custom robot in RViz.
- `scripts/drive_forward.sh`: Publishes `/cmd_vel` for a few seconds, then
  sends zero velocity.
- `scripts/send_nav_goal_forward.sh`: Sends a Nav2 goal a relative distance
  ahead of the robot start position.
- `docs/gazebo_environment_notes.md`: Most important recovered engineering log.
- `docs/地铁巡检项目资料/下午一点对话整理-地铁巡检学习与分工.txt`: Recovered
  earlier learning and team-division discussion.

## Simulation Status Recovered From Notes

The previous debugging work focused on making the robot visible, physically
stable, and controllable by Nav2.

Confirmed in the notes:

- `/cmd_vel` has a `train_diff_drive` subscriber.
- `/odom` is published by `train_diff_drive`.
- Manual `/cmd_vel linear.x=0.25` makes odometry `x` increase.
- Nav2 accepts a forward goal and logs `Goal succeeded`.

Important fixes already applied:

- Robot body collision was changed from STL mesh to a simple box.
- Wheel collision was changed from STL mesh to cylinders.
- Wheel contact stiffness was reduced to avoid Gazebo jitter.
- Wheel joints were reoriented for a normal differential-drive layout.
- Diff-drive plugin uses one active wheel joint per side, because the Humble
  plugin rejected the earlier four-joint config.
- Robot spawn yaw in the tunnel was changed from `1.571` to `0`, so it starts
  facing along the tunnel.
- Nav2 goal tolerance was tightened from `0.35` to `0.12`.
- Forward goal script now converts a relative distance into an absolute odom
  target using the robot start x position, approximately `-38.0`.

## Useful Commands

Open only the Gazebo tunnel:

```bash
cd ~/my-project/subway-patrol-robot-sim
./scripts/open_subway_tunnel.sh
```

Open Gazebo, TF publisher, and RViz:

```bash
cd ~/my-project/subway-patrol-robot-sim
./scripts/open_gazebo_rviz_lidar.sh
```

Open Gazebo, TF publisher, Nav2, and RViz:

```bash
cd ~/my-project/subway-patrol-robot-sim
./scripts/open_nav2_demo.sh
```

Open the imported custom robot in Gazebo preview:

```bash
cd ~/my-project/subway-patrol-robot-sim
./scripts/open_custom_robot_preview.sh
```

Open the imported custom robot in RViz preview:

```bash
cd ~/my-project/subway-patrol-robot-sim
./scripts/open_rviz_robot.sh
```

Manual drive test:

```bash
./scripts/drive_forward.sh 3 0.25
```

Send a Nav2 goal 4 meters forward from the start position:

```bash
./scripts/send_nav_goal_forward.sh 4.0
```

## Competition Learning Context

The user is on the algorithm side. Prior advice recovered from the notes:

- Learn YOLO deeply for object-like defects such as fastener missing/loose,
  support looseness, and foreign-object intrusion.
- Learn segmentation alongside YOLO for cracks and water leakage, because these
  defects are thin or irregular and are poorly represented by bounding boxes.
- Learn OpenCV with a focused scope: preprocessing, low-light enhancement,
  camera calibration, undistortion, and projection geometry.
- Learn ROS2 only to the level needed to use topics, nodes, TF, and simulation
  outputs. It is infrastructure, not the main algorithm scoring item.
- Learn only the localization-relevant part of SLAM/navigation: coordinate
  transforms, odometry/IMU dead reckoning, lidar-camera calibration, and tunnel
  mileage/ring/clock-position mapping.

Suggested team split:

- Detection algorithm group: YOLO, segmentation, data labeling, recall, model
  export and acceleration.
- Fusion and localization group: calibration, point cloud basics, coordinate
  transforms, pixel-to-world/tunnel-position mapping.
- Simulation and robot group: ROS2, Gazebo/Unity, robot model, Nav2 demo, video.
- Platform and report group: visualization, standard inspection report output,
  industry standards, final technical report.

## Last Recovered Open Question

The previous conversation appears to have stopped at:

> 融合与定位这个我该怎么学？这个不属于slam吗？

Good next response:

- Explain that fusion/localization overlaps with SLAM but is not equal to full
  SLAM.
- For this competition, the practical goal is not necessarily to build a full
  SLAM system. The goal is to map detected defect pixels into a tunnel position:
  mileage, ring number, and clock direction.
- Recommended learning path: coordinate frames and homogeneous transforms,
  camera calibration, lidar-camera extrinsics, depth or point-cloud projection,
  odometry/IMU pose chain, then tunnel-specific position expression.
