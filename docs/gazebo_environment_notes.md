# Gazebo 地铁轨道环境

## 打开方式

在 WSL 终端执行：

```bash
cd ~/my-project/subway-patrol-robot-sim
./scripts/open_subway_tunnel.sh
```

也可以手动执行：

```bash
cd ~/my-project/subway-patrol-robot-sim
export GAZEBO_MODEL_PATH="$PWD/models:$GAZEBO_MODEL_PATH"
gazebo worlds/subway_track_tunnel.world
```

## 当前内容

- 长直轨道段
- 简化地铁隧道地面、侧墙、顶板
- 隧道灯光
- 简化巡检小车占位模型
- 裂缝、渗漏水、支架松脱的可视化标记

## SolidWorks 导入机器人预览

新增的 `custom_robot` 是从 SolidWorks 导出的机器人模型整理出的预览资源，当前定位是“看外观、调朝向、确认 mesh 路径”，还不是带控制器和传感器的可导航仿真车。

- Gazebo 静态预览入口：`./scripts/open_custom_robot_preview.sh`
- RViz 固定关节预览入口：`./scripts/open_rviz_robot.sh`
- Gazebo 模型：`models/custom_robot/model.sdf`
- RViz 预览 URDF：`urdf/custom_robot_gazebo_preview.urdf`
- 规范 mesh 目录：`models/custom_robot/meshes/`

注意：`urdf/custom_robot.urdf` 保留了原始导出结构，部分 mesh 路径仍指向 `车urdf(1)/meshes/`；预览脚本优先使用已经改到规范 mesh 目录的 `custom_robot_gazebo_preview.urdf`。

## 调车审核注释

这部分记录 `gazebo_train` 小车从“能显示”调整到“能被 Nav2 控制移动”的关键改动。这里只说明实验小车，不涉及 SolidWorks 导出的 `车urdf(1)`。

### `models/gazebo_train/model.sdf`

- `base_link` 的碰撞体从 STL mesh 改成 box。
  目的：Gazebo 的复杂 STL 碰撞容易造成车体和地面接触抖动；box 碰撞更稳定，视觉外观可以和碰撞体分开处理。
- 轮子碰撞体改成 cylinder，并把接触刚度从过硬的 `kp=1e+13` 降到 `kp=1e+06`。
  目的：降低轮子和轨道/地面接触时的数值震荡，减少“原地抽搐”。
- 轮子关节重新按差速车逻辑布置：前进方向是 `base_link` 的 `+X`，左右轮分布在 `Y` 轴两侧。
  目的：让 Nav2、`/cmd_vel linear.x`、Gazebo 差速插件对“前进方向”的理解一致。
- `libgazebo_ros_diff_drive.so` 保持每侧一个主动轮：`wheel_left_joint` 和 `wheel_right_joint`。
  目的：Humble 里的这个插件不接受我之前尝试的四轮 joint 配置；四轮写进去会导致 `Inconsistent number of joints specified`，插件直接不发布 `/odom`。
- Gazebo 可见外观改成简化蓝色车体和黑色圆柱轮。
  目的：避免旧白色 STL 外观方向和真实运动方向不一致，造成“看起来没动/轮子方向怪”的误判。

### `worlds/subway_track_tunnel.world`

- `inspection_robot_with_lidar` 的初始 yaw 从 `1.571` 改为 `0`。
  目的：让小车出生时沿隧道方向，而不是横着朝侧墙。

### `config/nav2_odom_params.yaml`

- `xy_goal_tolerance` 从 `0.35` 收紧到 `0.12`。
  目的：之前 RViz 里还剩 `0.32 m` 就会显示 `reached`，导致看起来“目标点发了但车不动”。收紧后，只有更接近目标才判定到达。

### `scripts/send_nav_goal_forward.sh`

- 目标点不再直接使用 `x=距离`，而是用出生点 `START_X=-38.0` 加上前进距离。
  目的：当前 Nav2 使用 `odom` 坐标，小车出生 odom 约为 `x=-38`；如果直接发 `x=4`，实际目标是 42 米外，不是前进 4 米。

### `scripts/drive_forward.sh`

- 从只发一次 `/cmd_vel` 改成持续发布几秒再停车。
  目的：只发一次速度命令太短，Gazebo 中很容易看起来像没动；持续发布更适合测试底盘是否能走。

### 当前已验证结果

- `/cmd_vel` 有 `train_diff_drive` 订阅。
- `/odom` 由 `train_diff_drive` 发布。
- 手动发送 `/cmd_vel linear.x=0.25` 后，`/odom` 的 `x` 会向前增加。
- Nav2 接受前方目标后，日志出现 `Goal succeeded`。

## 代码差异附件

下面用代码审核常见的 `diff` 形式记录关键修改。红色 `-` 表示删掉或替换的旧写法，绿色 `+` 表示新增或修改后的写法。

### 1. 底盘碰撞体：STL 改为简单 box

文件：`models/gazebo_train/model.sdf`

```diff
- <mesh>
-   <scale>0.001 0.001 0.001</scale>
-   <uri>model://gazebo_train/meshes/waffle_custom_base.stl</uri>
- </mesh>
+ <box>
+   <size>1.20 0.70 0.20</size>
+ </box>
```

作用：STL mesh 适合显示外观，但不适合直接做物理碰撞。复杂 mesh 和地面接触时容易让 Gazebo 数值求解不稳定，表现为车体抖动、弹跳或原地抽搐。改成 box 后，碰撞计算更简单，底盘更稳。

### 2. 轮子碰撞体：STL 改为 cylinder

文件：`models/gazebo_train/model.sdf`

```diff
- <mesh>
-   <scale>0.001 0.001 0.001</scale>
-   <uri>model://gazebo_train/meshes/left_tire.stl</uri>
- </mesh>
+ <cylinder>
+   <radius>0.105</radius>
+   <length>0.08</length>
+ </cylinder>
```

作用：轮子真正参与运动的是碰撞体，不只是视觉模型。用圆柱体可以让 Gazebo 明确知道“这是一个轮子”，比 STL 轮胎 mesh 更稳定，也更符合差速小车的物理模型。

### 3. 轮子接触参数：降低过硬接触

文件：`models/gazebo_train/model.sdf`

```diff
- <kp>1e+13</kp>
- <kd>1</kd>
- <max_vel>0.01</max_vel>
- <min_depth>0</min_depth>
+ <kp>1e+06</kp>
+ <kd>10</kd>
+ <max_vel>0.1</max_vel>
+ <min_depth>0.001</min_depth>
```

作用：原来的 `kp=1e+13` 太硬，Gazebo 会非常激烈地修正轮子和地面的接触误差，容易出现高频抖动。降低刚度、增加阻尼后，轮子和地面的接触更“软”，小车移动更平顺。

### 4. 轮子关节方向：改成标准差速车方向

文件：`models/gazebo_train/model.sdf`

```diff
- <pose relative_to='base_footprint'>-0.22 -0.4 0.1 -1.5708 0 0</pose>
- <axis>
-   <xyz>1 0 0</xyz>
- </axis>
+ <pose relative_to='base_footprint'>0.35 0.25 0.105 0 0 0</pose>
+ <axis>
+   <xyz>0 1 0</xyz>
+ </axis>
```

作用：Nav2 和 `cmd_vel` 默认认为机器人沿 `base_link` 的 `+X` 方向前进。修改后，左右轮分布在 `Y` 轴两侧，轮轴沿 `Y` 方向，车体沿 `+X` 前进。这是标准差速车坐标关系。

### 5. 差速插件：保持每侧一个主动轮

文件：`models/gazebo_train/model.sdf`

```diff
  <left_joint>wheel_left_joint</left_joint>
- <left_joint>wheel_left2_joint</left_joint>
  <right_joint>wheel_right_joint</right_joint>
- <right_joint>wheel_right2_joint</right_joint>
```

作用：我一开始尝试让插件同时控制四个轮子，但 Humble 的 `libgazebo_ros_diff_drive.so` 对这个配置报错：`Inconsistent number of joints specified`。报错后插件不会订阅 `/cmd_vel`，也不会发布 `/odom`。所以这里恢复为每侧一个主动轮，后轮作为自由滚动支撑轮。

### 6. 小车初始朝向：沿隧道方向出生

文件：`worlds/subway_track_tunnel.world`

```diff
- <pose>-38 -0.018 0.12 0 0 1.571</pose>
+ <pose>-38 -0.018 0.12 0 0 0</pose>
```

作用：`1.571` 约等于 90 度，会让小车出生时横着朝侧墙。改成 `0` 后，小车出生方向和隧道方向一致，RViz 目标点、Gazebo 运动方向、Nav2 的 `odom` 坐标更容易对应起来。

### 7. Nav2 目标容差：避免太早判定到达

文件：`config/nav2_odom_params.yaml`

```diff
- xy_goal_tolerance: 0.35
+ xy_goal_tolerance: 0.12
```

作用：截图里 RViz 显示剩余距离 `0.32 m`，但旧容差是 `0.35 m`，所以 Nav2 会直接显示 `reached`，看起来像车没有动。收紧到 `0.12 m` 后，机器人需要更接近目标才算到达。

### 8. 前进目标脚本：从出生点计算目标

文件：`scripts/send_nav_goal_forward.sh`

```diff
- DISTANCE="${1:-4.0}"
+ DISTANCE="${1:-4.0}"
+ START_X="${START_X:--38.0}"
+ GOAL_X="$(awk -v start="${START_X}" -v distance="${DISTANCE}" 'BEGIN { printf "%.3f", start + distance }')"
...
- position: {x: ${DISTANCE}, y: 0.0, z: 0.0},
+ position: {x: ${GOAL_X}, y: -0.018, z: 0.0},
```

作用：小车出生时 `/odom` 的 `x` 大约是 `-38`。如果脚本直接把目标发成 `x=4`，实际不是“前进 4 米”，而是让车从 `-38` 跑到 `4`，距离约 42 米。现在脚本会把输入距离换算成相对出生点的目标。

### 9. 手动测试脚本：持续发速度再停车

文件：`scripts/drive_forward.sh`

```diff
- ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
-   "{linear: {x: 0.35, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
+ timeout "${DURATION}" ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist \
+   "{linear: {x: ${SPEED}, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}" || true
+
+ ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
+   "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

作用：只发一次 `/cmd_vel` 时间太短，Gazebo 里肉眼很难看到移动。持续发布几秒后再发 0 速度停车，更适合检查底盘是否真的能走。

## 模型来源

轨道 mesh 来自开源仓库：

```text
https://github.com/LuigiFerraioli/ros2_gazebo_train
```

该仓库为 MIT License。这里没有引入它的 ROS2 启动系统，只复用 Gazebo 轨道模型，并在本项目中重写了可直接打开的 Gazebo Classic world。
