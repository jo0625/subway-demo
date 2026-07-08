# Vision Demo

这个目录是视觉板块的第一个“可运行样机”，作用是先把病害检测流程跑通。

它现在还不是正式算法，也不是 ROS2 实时视觉节点：

- 不是 YOLO/分割模型推理。
- 不订阅 Gazebo 相机话题。
- 不代表真实数据集上的检测精度。

它现在做的是一条最小视觉流程：

1. 生成一张合成的地铁隧道图像。
2. 在图像中模拟裂缝、渗漏水、支架松脱三类病害。
3. 用 OpenCV 灰度、HSV 颜色阈值、轮廓规则检测病害。
4. 输出原图、检测标注图和 JSON 结构化结果。

更完整的视觉板块说明见：

```text
docs/vision_module_notes.md
```

运行：

```bash
python3 vision_demo/synthetic_defect_demo.py
```

输出文件会生成在：

```text
vision_demo/output/
```

主要输出：

- `synthetic_tunnel.png`: 原始合成图。
- `synthetic_tunnel_annotated.png`: 检测结果画框图。
- `detections.json`: 检测结果，供后续融合定位或平台组读取。

也可以传入自己的图片试试：

```bash
python3 vision_demo/synthetic_defect_demo.py --image path/to/image.png
```

## 代码怎么读

- `create_synthetic_tunnel()`: 造一张假的隧道图，并画上三类病害。
- `detect_defects()`: 核心检测逻辑，分别生成裂缝、渗漏水、支架松脱的 mask。
- `contour_detections()`: 把 mask 中的连通区域转成检测框、面积和置信度。
- `draw_detections()`: 把检测框和类别文字画回图片上。
- `main()`: 处理命令行参数，写出图片和 JSON。

## 下一步方向

正式版本应该沿这个方向替换和升级：

1. 用 Gazebo 相机或真实视频作为输入。
2. 用 YOLO 检测目标型病害，例如支架松脱、异物侵限、扣件缺失。
3. 用分割模型处理裂缝、渗漏水这类细长或不规则病害。
4. 把检测结果发布成 ROS2 topic，供定位、融合、平台展示使用。

## ROS2 节点试运行

`vision_node.py` 是一个 ROS2 包装节点。它复用当前 OpenCV 检测逻辑，并把结果发布成 `/detections` JSON 字符串。

默认模式不需要打开 Gazebo，会每秒生成一张合成隧道图做检测：

```bash
./scripts/run_vision_node.sh
```

另开终端查看检测结果：

```bash
source /opt/ros/humble/setup.bash
ros2 topic echo /detections
```

节点还会发布带框图片：

```text
/vision/annotated_image
```

同时会把最新一帧保存到：

```text
vision_demo/output/vision_node_latest_annotated.png
vision_demo/output/vision_node_latest_detections.json
```

以后接 Gazebo 相机时，把合成图模式关掉，并指定相机 topic：

```bash
./scripts/run_vision_node.sh --ros-args -p use_synthetic:=false -p image_topic:=/zed2i_depth/image_raw
```
