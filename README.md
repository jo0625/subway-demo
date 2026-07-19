# subway-demo

本分支用于地铁巡检机器人的 Gazebo 仿真，包括隧道场景、简化巡检车辆、激光雷达、Nav2 直行导航和轨道障碍安全停车模块。

## 基础隧道仿真

在第一个终端启动 Gazebo：

```bash
cd ~/my-project/subway-patrol-robot-sim/subway-patrol-robot-sim-simulation
./scripts/open_subway_tunnel.sh
```

Gazebo 完全打开后，在第二个终端让车辆前进：

```bash
cd ~/my-project/subway-patrol-robot-sim/subway-patrol-robot-sim-simulation
./scripts/drive_forward.sh 10 0.4
```

参数说明：

- `10`：移动时间，单位为秒。
- `0.4`：前进速度，单位为米/秒。
- 脚本会等待 Gazebo 的速度订阅者，运行结束后自动发送停车命令。
- 启动和驾驶脚本默认使用 `ROS_DOMAIN_ID=0` 进行 WSL 本机 DDS 通信。

关闭 Gazebo：

```bash
pkill -x gzclient
pkill -x gzserver
```

## Nav2 安全导航演示

默认使用演示参数：障碍持续 10 秒后报告，速度 watchdog 超时为 2 秒。

```bash
cd ~/my-project/subway-patrol-robot-sim/subway-patrol-robot-sim-simulation
bash scripts/open_nav2_demo.sh
```

使用生产参数配置启动：

```bash
TUNNEL_GUARD_PROFILE=production bash scripts/open_nav2_demo.sh
```

生产配置当前使用 30 秒障碍报告和 0.5 秒 watchdog；迁移真机前仍需根据通信抖动和制动距离重新验收。

安全命令链：

```text
Nav2 /cmd_vel
→ tunnel_obstacle_guard
→ /cmd_vel_safe
→ cmd_vel_watchdog
→ /cmd_vel_drive
→ train_planar_move
→ 车辆
```

## 导航与安全测试代码清单

除启动命令外，以下命令均在新终端执行。每个新终端先加载 ROS 2：

```bash
source /opt/ros/humble/setup.bash
cd ~/my-project/subway-patrol-robot-sim/subway-patrol-robot-sim-simulation
```

### 1. 节点和安全命令链

```bash
ros2 lifecycle get /bt_navigator
ros2 action info /navigate_to_pose
ros2 topic info /cmd_vel_safe
ros2 topic info /cmd_vel_drive
```

预期：`bt_navigator` 为 `active [3]`；导航 Action server 数量为 1；两个安全速度话题均为 1 个发布者和 1 个订阅者。

### 2. 检查运行参数

```bash
ros2 param get /tunnel_obstacle_guard report_after
ros2 param get /tunnel_obstacle_guard stop_distance
ros2 param get /cmd_vel_watchdog timeout
ros2 param get /local_costmap/local_costmap obstacle_layer.scan.inf_is_valid
ros2 param get /global_costmap/global_costmap obstacle_layer.scan.inf_is_valid
```

Demo 预期值依次为 `10.0`、`2.0`、`2.0`、`True`、`True`。

### 3. 无障碍直行导航

前进 1 米，整个任务最多等待 120 秒：

```bash
bash scripts/send_nav_goal_forward.sh 1.0 120
```

预期车辆只沿轨道正向直行，最终显示：

```text
Navigation succeeded
```

### 4. 障碍停车、错误报告和恢复

先读取车辆位置：

```bash
ros2 topic echo /odom --once --field pose.pose.position
```

障碍应提前生成在车辆前方约 5 米，以下坐标适用于车辆起点约 `x=-20` 的情况：

```bash
python3 scripts/manage_nav_test_obstacle.py delete
python3 scripts/manage_nav_test_obstacle.py spawn --x -15.0 --y 0.0
```

在另一个终端提前监听错误报告：

```bash
ros2 topic echo /navigation/obstacle_error
```

发送会穿过障碍位置的 7 米导航目标：

```bash
bash scripts/send_nav_goal_forward.sh 7.0 120
```

车辆应在障碍前停车且不转向、不后退。保留障碍至少 10 秒，预期收到：

```text
NAVIGATION_BLOCKED: reason=front_obstacle duration=10...
```

收到报告后删除障碍：

```bash
date '+删除开始：%H:%M:%S.%3N'
python3 scripts/manage_nav_test_obstacle.py delete
date '+删除完成：%H:%M:%S.%3N'
```

预期 Costmap 清除旧障碍，车辆恢复直行，原导航任务最终成功。

### 5. 转向、倒车和超速过滤

先持续观察守卫输出：

```bash
ros2 topic echo /cmd_vel_safe
```

转向输入应被改成纯直行：

```bash
timeout 2 ros2 topic pub -r 50 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.5}}"
```

倒车输入应被改成零速度：

```bash
timeout 2 ros2 topic pub -r 50 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: -0.2}, angular: {z: 0.0}}"
```

超速输入应被限制为 `0.35 m/s`：

```bash
timeout 2 ros2 topic pub -r 50 /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 1.0}, angular: {z: 0.0}}"
```

### 6. 隔离测试雷达中断保护

该测试使用 `/test_*` 话题，不会驱动真实 Gazebo 底盘。

终端 A启动隔离守卫：

```bash
python3 scripts/tunnel_obstacle_guard.py --ros-args \
  -r __node:=guard_scan_timeout_test \
  -r /scan:=/test_scan \
  -r /cmd_vel:=/test_cmd_vel \
  -r /cmd_vel_safe:=/test_cmd_vel_safe \
  -r /navigation/obstacle_error:=/test_obstacle_error \
  -p use_sim_time:=false \
  -p scan_timeout:=2.0
```

终端 B模拟正常雷达：

```bash
ros2 topic pub -r 10 /test_scan sensor_msgs/msg/LaserScan \
  "{angle_min: -0.5, angle_max: 0.5, angle_increment: 0.5, range_min: 0.1, range_max: 10.0, ranges: [5.0, 5.0, 5.0]}"
```

终端 C持续发送测试速度：

```bash
ros2 topic pub -r 10 /test_cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.0}}"
```

终端 D观察隔离输出：

```bash
ros2 topic echo /test_cmd_vel_safe
```

停止终端 B的雷达发布后，约 2 秒应输出零速度并记录 `scan_stale`；恢复雷达发布后应重新允许 `0.2 m/s`。

### 7. Watchdog 守卫失联测试

警告：这是破坏性测试，会故意终止安全守卫。测试结束后必须重启整套仿真。

先发送较长导航目标：

```bash
bash scripts/send_nav_goal_forward.sh 4.0 120
```

车辆运动时在另一终端终止守卫：

```bash
pkill -f tunnel_obstacle_guard.py
```

预期 watchdog 在配置的超时时间后输出：

```text
Safe command stream timed out ...; forcing stop
```

检查最终底盘命令：

```bash
ros2 topic echo /cmd_vel_drive --once
```

所有线速度和角速度都应为零。

### 8. 发布频率检查

```bash
timeout 30 ros2 topic hz /scan
timeout 30 ros2 topic hz /cmd_vel_safe
timeout 30 ros2 topic hz /cmd_vel_drive
```

频率测试应同时关注平均频率和最大消息间隔；watchdog 超时必须大于正常系统的最坏消息间隔并保留合理余量。

## 静态检查

```bash
python3 -m py_compile \
  scripts/cmd_vel_watchdog.py \
  scripts/manage_nav_test_obstacle.py \
  scripts/send_nav_goal_forward.py \
  scripts/tunnel_obstacle_guard.py

bash -n scripts/open_nav2_demo.sh scripts/send_nav_goal_forward.sh

python3 -c "import xml.etree.ElementTree as E; E.parse('models/gazebo_train/model.sdf')"

python3 -c "import yaml; [yaml.safe_load(open(p)) for p in [\
  'config/nav2_odom_params.yaml', \
  'config/tunnel_guard_demo.yaml', \
  'config/tunnel_guard_production.yaml']]"
```

## 主要文件

- `models/subway_tunnel/`：带贴图的隧道模型及碰撞模型。
- `models/gazebo_train/model.sdf`：巡检车辆、传感器和最终底盘速度话题配置。
- `worlds/subway_track_tunnel.world`：正式隧道仿真场景。
- `config/nav2_odom_params.yaml`：Nav2、Footprint、Obstacle Layer 和 clearing 参数。
- `config/tunnel_guard_demo.yaml`：WSL 演示安全参数。
- `config/tunnel_guard_production.yaml`：生产候选安全参数。
- `scripts/open_nav2_demo.sh`：启动 Gazebo、RSP、守卫、watchdog、Nav2 和 RViz。
- `scripts/tunnel_obstacle_guard.py`：直行限制、障碍停车和错误报告。
- `scripts/cmd_vel_watchdog.py`：安全守卫失联后的软件停车保护。
- `scripts/send_nav_goal_forward.py`：根据当前里程计发送相对导航目标。
- `scripts/manage_nav_test_obstacle.py`：生成和删除测试障碍物。
