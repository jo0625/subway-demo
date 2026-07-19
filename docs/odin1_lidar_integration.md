# ODIN1 激光雷达：仿真、实机与 ROS 2 接入笔记

## 1. 文档目标

本文档用于记录 ODIN1 激光雷达在地铁巡检机器人项目中的接入思路，覆盖：

- 如何判断能否直接用 USB 连接电脑；
- 如何获取和检查官方 ROS 驱动；
- 仿真雷达、实机雷达和 mapping/Nav2 的关系；
- 项目中应该新增哪些 ROS 2 包和文件；
- 如何验证话题、消息类型、TF、频率和时间；
- 如何在仿真模式与实机模式之间切换；
- 如何录制实机数据并离线回放。

设备与官方资料：

- 型号：Manifold Tech ODIN1
- 产品文档：<https://manifoldtechltd.github.io/wiki/odin_series/odin1/>
- 官方 ROS 驱动：<https://github.com/manifoldsdk/odin_ros_driver>

> 注意：必须以产品说明书和官方驱动 README 为准。不要根据接口外形猜测供电电压、数据接口或网络参数。

## 2. 先理解“连接”的含义

雷达接入 ROS 通常包含三层连接：

```text
物理连接：ODIN1 雷达 -> USB/网线/供电 -> 运行 ROS 的电脑
驱动连接：官方驱动读取设备数据 -> 发布 ROS 话题
软件连接：mapping/Nav2/RViz -> 订阅标准 ROS 话题
```

“仿真连接现实”通常不是让 Gazebo 直接控制真实雷达，而是让仿真和实机提供相同的软件接口：

```text
Gazebo 雷达插件 ─┐
                  ├─> 标准话题 ─> mapping / Nav2 / RViz
ODIN1 官方驱动 ──┘
```

正常运行时只启用其中一个数据源。

## 3. ODIN1 能否直接通过 USB 连接电脑

只有官方说明明确指出 USB 是数据接口，并且设备供电满足要求时，才可以直接连接。

USB 接口可能有以下用途：

1. USB 数据和供电一体；
2. USB 只传输数据，雷达需要独立供电；
3. USB 仅用于调试、升级固件或配置；
4. 外观类似 USB 的接口实际使用厂商专用线缆。

因此，在接线前需要从产品页面或铭牌确认：

- 数据接口类型；
- 雷达工作电压和最大功耗；
- USB 是否可以直接供电；
- 是否需要独立电源；
- 是否需要 USB 转串口驱动；
- 是否需要配置固定 IP；
- 接口定义和线缆方向。

### 3.1 USB 接入后的检查

连接后先不要急着启动 ROS 驱动，执行：

```bash
lsusb
dmesg --follow
```

另开终端检查设备文件：

```bash
ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null
```

可能出现的情况：

- `lsusb` 出现新设备，但没有 `/dev/ttyUSB*`：它可能不是串口设备；
- 出现 `/dev/ttyUSB0`：驱动可能通过串口读取；
- 出现 `/dev/ttyACM0`：驱动可能通过 USB CDC ACM 读取；
- 完全没有新设备：检查供电、线缆、接口用途和内核日志；
- 设备不断断开重连：可能是供电不足、线缆问题或 USB 省电设置。

如果驱动提示权限不足，可以临时检查：

```bash
groups
ls -l /dev/ttyUSB0
```

长期方案应使用正确的用户组或 udev 规则，不建议长期使用 `sudo ros2 ...`。

### 3.2 网口接入后的检查

如果 ODIN1 使用网口传输数据，雷达和电脑必须在兼容的子网中：

```bash
ip -br addr
ip neigh
ping <雷达IP>
```

需要从官方文档确认：

- 雷达默认 IP；
- 电脑应该设置的静态 IP；
- 子网掩码；
- 数据 UDP 端口；
- 配置端口；
- 是否允许修改雷达 IP。

不要在不知道默认 IP 的情况下随意修改系统网络配置。

## 4. 官方驱动应该放在哪里

建议把官方驱动放进当前 simulation ROS 2 工作空间的 `src/`：

```text
subway-patrol-robot-sim-simulation/
└── src/
    ├── odin_ros_driver/                 # 官方驱动
    ├── subway_patrol_description/       # 机器人模型与传感器 TF
    ├── subway_patrol_simulation/        # Gazebo 仿真
    └── subway_patrol_lidar_bringup/     # 项目自己的启动与适配
```

获取驱动：

```bash
source /opt/ros/humble/setup.bash
cd /home/jo/my-project/subway-patrol-robot-sim/subway-patrol-robot-sim-simulation/src
git clone https://github.com/manifoldsdk/odin_ros_driver.git
```

下载后先阅读官方说明，不要立刻修改驱动源码：

```bash
cd odin_ros_driver
find . -maxdepth 3 -type f | sort
sed -n '1,240p' README.md
find . -name package.xml -print
find . -path '*/launch/*' -type f -print
find . \( -name '*.yaml' -o -name '*.json' \) -print
```

需要从 README 记录以下信息：

```text
支持的 ROS 版本：
驱动包名：
可执行程序名：
launch 文件名：
USB 设备路径或雷达 IP：
默认数据话题：
消息类型：LaserScan / PointCloud2 / 厂商自定义消息
frame_id：
默认频率：
是否发布 intensity：
是否发布 IMU：
```

## 5. 构建官方驱动

回到工作空间根目录：

```bash
cd /home/jo/my-project/subway-patrol-robot-sim/subway-patrol-robot-sim-simulation
source /opt/ros/humble/setup.bash
```

如果驱动 README 要求安装依赖，优先使用 README 给出的命令。常规 ROS 2 工作空间可以检查依赖：

```bash
rosdep install --from-paths src --ignore-src -r -y
```

然后构建：

```bash
colcon build --symlink-install
source install/setup.bash
```

构建完成后检查：

```bash
ros2 pkg list | grep -i odin
ros2 pkg executables | grep -i odin
```

## 6. 不要自己从零编写雷达协议节点

官方驱动已经负责：

- 打开 USB、串口或网络设备；
- 接收雷达原始数据包；
- 解析厂商协议；
- 生成时间戳；
- 发布 LaserScan 或 PointCloud2；
- 输出设备诊断和错误信息。

项目自己需要编写或配置的是：

- 启动官方驱动的 launch；
- 雷达参数 YAML；
- 话题 remap；
- `base_link -> laser_link` TF；
- PointCloud2 到 LaserScan 的转换（如果需要）；
- 仿真/实机模式切换。

## 7. 新建项目级雷达 bringup 包

创建包：

```bash
source /opt/ros/humble/setup.bash
cd /home/jo/my-project/subway-patrol-robot-sim/subway-patrol-robot-sim-simulation/src

ros2 pkg create \
  --build-type ament_cmake \
  subway_patrol_lidar_bringup

cd subway_patrol_lidar_bringup
mkdir launch config rviz
touch launch/odin1_real.launch.py
touch launch/lidar_pipeline.launch.py
touch config/odin1.yaml
```

目录结构：

```text
subway_patrol_lidar_bringup/
├── CMakeLists.txt
├── package.xml
├── config/
│   └── odin1.yaml
├── launch/
│   ├── odin1_real.launch.py
│   └── lidar_pipeline.launch.py
└── rviz/
```

这个包初期可以只有 launch 和 YAML，不需要创建 C++ 或 Python 数据发布节点。

### 7.1 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.8)
project(subway_patrol_lidar_bringup)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY launch config rviz
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
```

### 7.2 package.xml 依赖

在生成的文件中加入：

```xml
<exec_depend>launch</exec_depend>
<exec_depend>launch_ros</exec_depend>
<exec_depend>ament_index_python</exec_depend>
<exec_depend>robot_state_publisher</exec_depend>
<exec_depend>sensor_msgs</exec_depend>
<exec_depend>tf2_ros</exec_depend>
<exec_depend>pointcloud_to_laserscan</exec_depend>
```

确认官方驱动的 ROS 包名后，再加入对应的 `exec_depend`。

### 7.3 odin1.yaml

不要猜测厂商参数名称。应复制官方驱动仓库中的示例配置，再修改：

```text
设备路径或雷达 IP
主机 IP
数据端口
frame_id
扫描频率
回波模式
时间戳模式
发布话题
```

建议项目统一使用：

```text
雷达坐标系：laser_link
三维点云：/lidar/points
二维扫描：/scan
```

### 7.4 odin1_real.launch.py

下面是结构模板，必须用官方 README 中的真实名称替换占位符：

```python
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    config_file = os.path.join(
        get_package_share_directory("subway_patrol_lidar_bringup"),
        "config",
        "odin1.yaml",
    )

    driver = Node(
        package="REPLACE_WITH_OFFICIAL_PACKAGE",
        executable="REPLACE_WITH_OFFICIAL_EXECUTABLE",
        name="odin1_driver",
        output="screen",
        parameters=[config_file, {"use_sim_time": False}],
        remappings=[
            ("REPLACE_WITH_OFFICIAL_TOPIC", "/lidar/points"),
        ],
    )

    return LaunchDescription([driver])
```

如果官方仓库已经提供 launch 文件，优先 include 官方 launch，而不是重复拼装内部节点。

## 8. 当前仿真雷达状态

当前 Gazebo 模型文件：

```text
models/gazebo_train/model.sdf
```

当前参数：

```text
传感器类型：ray（二维扫描）
ROS 消息：sensor_msgs/LaserScan
话题：/scan
frame_id：laser_link
频率：10 Hz
水平采样：1024
水平视场：约 360°
最小距离：0.5 m
最大距离：120 m
高斯噪声标准差：0.01 m
```

相关文件：

- `models/gazebo_train/model.sdf`：Gazebo 雷达物理模型和发布插件；
- `src/subway_patrol_description/urdf/gazebo_train_tf.urdf`：机器人和雷达安装 TF；
- `config/gazebo_lidar.rviz`：RViz 的 `/scan` 显示；
- `config/nav2_odom_params.yaml`：Nav2 障碍层订阅 `/scan`；
- `scripts/publish_fake_scan.sh`：不启动 Gazebo 时发布测试扫描。

官方 ODIN1 参数确认后，应调整仿真中的频率、视场、扫描点数、量程和噪声。

## 9. LaserScan 与 PointCloud2 的处理

启动官方驱动后检查：

```bash
ros2 node list
ros2 topic list -t
ros2 topic info -v <雷达话题>
ros2 topic echo <雷达话题> --once
ros2 topic hz <雷达话题>
```

### 9.1 官方驱动输出 LaserScan

如果消息类型是：

```text
sensor_msgs/msg/LaserScan
```

将官方话题 remap 为 `/scan`。当前 Nav2 和 RViz 可以直接使用。

### 9.2 官方驱动输出 PointCloud2

如果消息类型是：

```text
sensor_msgs/msg/PointCloud2
```

建议保留原始点云：

```text
/lidar/points
```

三维 mapping 直接订阅点云。Nav2 如果仍使用二维障碍层，可以通过 `pointcloud_to_laserscan` 生成 `/scan`：

```python
from launch_ros.actions import Node

pointcloud_to_scan = Node(
    package="pointcloud_to_laserscan",
    executable="pointcloud_to_laserscan_node",
    name="pointcloud_to_laserscan",
    output="screen",
    parameters=[{
        "target_frame": "laser_link",
        "transform_tolerance": 0.05,
        "min_height": -0.2,
        "max_height": 0.2,
        "angle_min": -3.14159,
        "angle_max": 3.14159,
        "angle_increment": 0.00436,
        "scan_time": 0.1,
        "range_min": 0.5,
        "range_max": 120.0,
        "use_inf": True,
        "use_sim_time": False,
    }],
    remappings=[
        ("cloud_in", "/lidar/points"),
        ("scan", "/scan"),
    ],
)
```

高度范围、角度、频率和量程必须根据实际安装位置与官方规格调整。

## 10. 仿真和实机的切换规则

### 10.1 仿真模式

```text
启动 Gazebo 雷达插件
不启动 ODIN1 官方驱动
use_sim_time = true
订阅 /clock
```

### 10.2 实机模式

```text
不启动 Gazebo 雷达插件
启动 ODIN1 官方驱动
use_sim_time = false
使用系统时间或雷达硬件时间
```

### 10.3 同时对比

如果需要同时查看，必须使用不同话题：

```text
/sim/scan
/real/scan
```

或者：

```text
/sim/lidar/points
/real/lidar/points
```

不要让两个发布者同时发布同一个 `/scan` 或 `/lidar/points`，否则 mapping 会收到互相冲突的数据。

## 11. TF 与安装标定

仿真和实机都应提供：

```text
base_link -> laser_link
```

仿真使用设计值；实机需要测量雷达相对于车体的位置和方向：

```text
x：向前为正
y：向左为正
z：向上为正
roll：绕 X 轴
pitch：绕 Y 轴
yaw：绕 Z 轴
```

建议将实测外参写入统一的 URDF/Xacro，由 `robot_state_publisher` 发布。不要同时用 URDF 和 `static_transform_publisher` 重复发布同一条 TF。

验证：

```bash
ros2 run tf2_ros tf2_echo base_link laser_link
```

常见 TF 问题：

- RViz 显示 `No transform`；
- 点云方向与车头相反；
- 障碍物相对车体偏移；
- 建图出现双墙和重影；
- 机器人运动时点云漂移。

## 12. 实机与仿真的主要区别

| 项目 | Gazebo 仿真 | ODIN1 实机 |
|---|---|---|
| 数据来源 | Gazebo 插件 | 官方硬件驱动 |
| 时间 | `/clock` | 系统/雷达时间 |
| `use_sim_time` | `true` | `false` |
| 安装外参 | 理想设计值 | 实际测量值 |
| 噪声 | 人工高斯噪声 | 反射、灰尘、玻璃和多径 |
| 数据频率 | 较稳定 | 可能波动 |
| 丢包 | 通常没有 | USB/网络可能丢包 |
| 延迟 | 通常较小 | 有传输、解析和处理延迟 |
| 运动畸变 | 通常被简化 | 移动扫描时可能明显 |
| 强度值 | 可能没有或理想化 | 与材质、距离相关 |
| 参数来源 | SDF 配置 | 固件和驱动配置 |

## 13. 多电脑 ROS 2 通信

如果 ODIN1 驱动运行在车载电脑，而 RViz/mapping 运行在另一台电脑：

```bash
export ROS_DOMAIN_ID=20
export ROS_LOCALHOST_ONLY=0
```

两台电脑必须：

- 使用相同 `ROS_DOMAIN_ID`；
- 位于可互通的网络；
- 可以互相 ping；
- 系统时间同步；
- 防火墙允许 ROS 2 DDS；
- 尽量使用有线网络。

注意区分两类网络：

```text
雷达数据网络：雷达 -> 驱动电脑
ROS 2 DDS 网络：驱动电脑 -> mapping/RViz 电脑
```

## 14. 实机 rosbag 回放

实机调通后建议立即录制：

```bash
ros2 bag record \
  /scan \
  /lidar/points \
  /tf \
  /tf_static \
  /odom \
  /imu/data
```

只保留实际存在的话题。

回放前关闭 Gazebo 雷达和真实雷达驱动：

```bash
ros2 bag play <bag目录>
```

rosbag 是连接仿真开发与实机验证最实用的方式：mapping 可以在没有雷达硬件时重复处理同一段真实数据。

## 15. 验收清单

### 硬件层

- [ ] 已确认 USB/网口的实际用途；
- [ ] 已确认供电电压与功耗；
- [ ] 电脑能识别设备或 ping 通雷达；
- [ ] 接口不会反复断连；
- [ ] 已记录雷达序列号和固件版本。

### 驱动层

- [ ] 官方驱动能在 ROS 2 Humble 构建；
- [ ] 驱动节点可以启动；
- [ ] 没有持续报设备、端口或权限错误；
- [ ] 已确认消息类型和话题；
- [ ] 已确认 `frame_id` 和频率；
- [ ] 已确认时间戳正常递增。

### TF 层

- [ ] 存在 `base_link -> laser_link`；
- [ ] 安装高度和方向与实物一致；
- [ ] 没有重复 TF 发布者；
- [ ] RViz 中点云方向正确。

### 软件接口层

- [ ] 二维扫描统一为 `/scan`；
- [ ] 三维点云统一为 `/lidar/points`；
- [ ] mapping 不依赖厂商原始话题名称；
- [ ] 仿真和实机不会同时发布同一个标准话题；
- [ ] 仿真 `use_sim_time=true`；
- [ ] 实机 `use_sim_time=false`。

### 仿真一致性

- [ ] Gazebo 的频率与实机一致；
- [ ] 水平/垂直视场与实机一致；
- [ ] 最小和最大量程与实机一致；
- [ ] 扫描点数/线数接近实机；
- [ ] TF 与实物安装一致；
- [ ] 加入了合理噪声。

## 16. 下一步需要从官方仓库确认的内容

下载并阅读 `odin_ros_driver` 后，填写：

```text
ROS 2 Humble 是否直接支持：TODO
官方包名：TODO
官方 executable：TODO
官方 launch 文件：TODO
默认设备接口：TODO
默认设备路径/IP：TODO
默认 ROS 话题：TODO
消息类型：TODO
默认 frame_id：TODO
频率和量程：TODO
官方示例 YAML 路径：TODO
```

在以上信息确认之前，不要把占位符 launch 当成可以直接运行的正式文件。
