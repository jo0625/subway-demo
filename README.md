# subway-demo

本分支用于地铁巡检机器人的 Gazebo 仿真，包括带贴图的新隧道、简化巡检小车和 ROS 2 控制脚本。

## 运行新隧道和简化小车

在第一个终端启动 Gazebo：

```bash
cd ~/my-project/subway-patrol-robot-sim/subway-patrol-robot-sim-simulation
./scripts/open_subway_tunnel.sh
```

等待 Gazebo 完全打开后，在第二个终端让车辆前进：

```bash
cd ~/my-project/subway-patrol-robot-sim/subway-patrol-robot-sim-simulation
./scripts/drive_forward.sh 10 0.4
```

参数说明：

- 第一个参数 `10`：移动时间，单位为秒。
- 第二个参数 `0.4`：前进速度，单位为米/秒。
- 脚本会等待 Gazebo 的 `/cmd_vel` 订阅者，运行结束后自动停车。
- 启动和驾驶脚本默认使用 `ROS_DOMAIN_ID=0` 与 WSL 本机 DDS 通信。

需要关闭 Gazebo 时：

```bash
pkill -x gzclient
pkill -x gzserver
```

## 主要文件

- `models/subway_tunnel/`：带贴图的隧道模型及碰撞模型。
- `models/gazebo_train/model.sdf`：简化巡检小车和传感器配置。
- `worlds/subway_track_tunnel.world`：新隧道、小车、灯光和隐藏承载面的正式场景。
- `scripts/open_subway_tunnel.sh`：启动 Gazebo 场景。
- `scripts/drive_forward.sh`：加载 ROS 2 环境并调用稳定控制节点。
- `scripts/drive_forward.py`：持续发布 `/cmd_vel` 并可靠停车。
