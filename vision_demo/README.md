# Vision Demo

这个目录是视觉板块的第一个最小 demo。它不依赖 YOLO 权重，也不需要训练数据，先用 OpenCV 做一个可运行的病害检测流程。

当前 demo 会做四件事：

1. 生成一张合成的地铁隧道图像。
2. 在图像中模拟裂缝、渗漏水、支架松脱三类病害。
3. 用简单的颜色/灰度/轮廓规则检测这些病害。
4. 输出标注图和 JSON 结果。

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

注意：这是规则 demo，只用于先跑通视觉流程。后续正式版本应替换为 YOLO/YOLO-seg/SegFormer 等模型。
