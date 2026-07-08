# 视觉板块说明

这份说明用来把当前 `vision-demo` 分支里的视觉部分讲清楚：它现在能做什么、还没做什么、和 Gazebo 仿真有什么关系，以及后续应该怎么升级。

## 当前定位

当前视觉板块是一个 OpenCV 最小样机，不是最终视觉系统。

它的价值是：

- 先证明“图像输入 -> 病害检测 -> 标注结果 -> JSON 输出”这条流程能跑通。
- 给团队一个可展示、可解释的视觉接口样子。
- 在还没有训练数据和 YOLO 权重之前，先让视觉板块不是空白。

它的限制也要讲清楚：

- 现在检测的是合成图片，不是真实相机画面。
- 现在算法是颜色、灰度和轮廓规则，不是深度学习模型。
- 现在结果没有和机器人位姿绑定，所以还不能自动给出真实隧道里程或世界坐标。

## 当前文件分工

- `vision_demo/synthetic_defect_demo.py`
  - 视觉 demo 主程序。
  - 可以自己生成一张隧道图，也可以读取外部图片。
  - 输出检测框图片和 `detections.json`。

- `vision_demo/README.md`
  - 运行入口说明。
  - 适合快速看命令、输出文件和代码结构。

- `scripts/run_vision_demo.sh`
  - 运行 demo 的包装脚本。
  - 等价于在项目根目录执行 `python3 vision_demo/synthetic_defect_demo.py`。

- `vision_demo/vision_node.py`
  - ROS2 视觉包装节点。
  - 复用 OpenCV demo 的检测函数。
  - 默认用合成图自测，发布 `/detections` 和 `/vision/annotated_image`。
  - 后续可以通过参数改成订阅 Gazebo 相机图像。

- `scripts/run_vision_node.sh`
  - 启动 `vision_node.py` 的包装脚本。
  - 会自动 source `/opt/ros/humble/setup.bash`。

- `models/gazebo_train/model.sdf`
  - 仿真小车模型。
  - 里面已经有一个深度相机传感器 `zed2i_depth`，Gazebo 理论上可以发布相机图像话题。

- `worlds/subway_track_tunnel.world`
  - 地铁隧道世界。
  - 里面有裂缝、渗漏水、支架松脱的三类可视化标记。

## 当前数据流

当前离线 demo 的数据流是：

```text
合成隧道图片
  -> OpenCV 规则检测
  -> 检测框和类别
  -> 标注图片
  -> detections.json
```

也就是说，它不依赖 ROS2，也不需要打开 Gazebo。

新增的 ROS2 节点数据流是：

```text
合成隧道图片
  -> vision_node.py
  -> OpenCV 规则检测
  -> /detections
  -> /vision/annotated_image
```

接入 Gazebo 相机后会变成：

```text
Gazebo 相机图像 topic
  -> vision_node.py
  -> OpenCV/YOLO/分割检测
  -> /detections
  -> /vision/annotated_image
```

运行后会得到类似这样的结构化结果：

```json
{
  "image_id": "synthetic_tunnel.png",
  "detection_count": 3,
  "detections": [
    {
      "type": "crack",
      "confidence": 0.98,
      "bbox": [191, 165, 99, 287],
      "area_px": 5057.5
    }
  ]
}
```

这里的 `bbox` 是图像坐标里的检测框：

```text
[左上角 x, 左上角 y, 宽度 w, 高度 h]
```

## 和 Gazebo 的关系

仓库里已经有两部分和视觉有关的 Gazebo 内容：

1. 小车模型里有相机：

```text
models/gazebo_train/model.sdf
camera_lens_link
sensor name="zed2i_depth"
plugin filename="libgazebo_ros_camera.so"
```

2. 隧道世界里有病害标记：

```text
worlds/subway_track_tunnel.world
defect_markers
crack_marker
leak_marker
loose_bracket_marker
```

但当前 `vision_demo/synthetic_defect_demo.py` 还没有接入这条 Gazebo 相机链路。

现在已经先补了一个 ROS2 包装节点 `vision_demo/vision_node.py`。它默认用合成图自测，后续可以通过参数订阅 Gazebo 相机：

```bash
./scripts/run_vision_node.sh --ros-args -p use_synthetic:=false -p image_topic:=/zed2i_depth/image_raw
```

所以现在的关系应该理解成：

```text
Gazebo 已经准备了相机和病害场景
OpenCV demo 已经准备了检测流程样机
vision_node.py 已经准备了 ROS2 包装层
下一步要确认 Gazebo 实际相机 topic 名称和图像内容
```

## 后续正式视觉系统

一个更完整的视觉板块可以拆成四层。

第一层：图像来源

- Gazebo 相机话题，例如 RGB 图、深度图、相机内参。
- 真实机器人相机视频。
- 离线测试图片或视频。

第二层：病害识别

- YOLO：适合支架松脱、异物侵限、扣件缺失等目标型病害。
- 分割模型：适合裂缝、渗漏水等细长、不规则病害。
- OpenCV：适合预处理、低照度增强、畸变校正、后处理。

第三层：结果表达

统一输出结构建议保持类似：

```json
{
  "stamp": "ROS time or image time",
  "frame_id": "camera_lens_link",
  "detections": [
    {
      "type": "crack",
      "confidence": 0.91,
      "bbox": [x, y, w, h],
      "mask": "optional segmentation mask",
      "area_px": 1234.5
    }
  ]
}
```

第四层：融合定位

后续融合组或定位组可以利用：

- 检测框或分割 mask 的像素位置。
- 相机内参。
- 深度图或激光雷达点云。
- 机器人在 `odom` 或 `map` 下的位姿。

最终把“图像里的病害”转换成“隧道里的位置”，例如：

```text
裂缝：里程 K12+034，左侧墙，约 9 点钟方向，高度 1.6 m
```

## 答辩时怎么讲

可以这样讲当前版本：

> 当前视觉分支先实现了一个 OpenCV 病害检测样机，用合成隧道图像模拟裂缝、渗漏水、支架松脱三类典型病害。程序会输出检测框标注图和 JSON 结构化结果。这个 demo 的重点不是最终精度，而是先跑通视觉算法的输入、检测、结果表达链路。后续会把图像输入从合成图替换为 Gazebo 相机或真实相机，并把规则检测替换为 YOLO 和分割模型。

这样讲比较稳，因为它不会把当前规则 demo 夸成已经完成的深度学习检测系统。

## 下一步建议

优先级从高到低：

1. 确认 Gazebo 相机实际发布的话题名和图像内容。
2. 用 `vision_node.py` 订阅 Gazebo 相机 topic，检查 `/vision/annotated_image` 是否正常。
3. 准备 YOLO 或分割模型接口，先支持加载权重，再替换规则检测。
4. 统一 `/detections` JSON 字段，和融合定位、平台展示组对齐。
