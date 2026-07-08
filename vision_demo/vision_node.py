#!/usr/bin/env python3
"""ROS2 wrapper for the OpenCV subway defect demo.

The node keeps the same simple JSON topic style as the teammate fake detection
publisher, but replaces hard-coded detections with detections from an image.
By default it uses synthetic images so the node can be tested without Gazebo.
Set use_synthetic:=false to subscribe to a camera topic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String

from synthetic_defect_demo import create_synthetic_tunnel, detect_defects, draw_detections


def ros_image_to_bgr(msg: Image) -> np.ndarray:
    """Convert a common ROS Image encoding into an OpenCV BGR image."""
    encoding = msg.encoding.lower()

    if encoding in ("bgr8", "rgb8"):
        channels = 3
        row = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)
        image = row[:, : msg.width * channels].reshape(msg.height, msg.width, channels).copy()
        if encoding == "rgb8":
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return image

    if encoding in ("bgra8", "rgba8"):
        channels = 4
        row = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)
        image = row[:, : msg.width * channels].reshape(msg.height, msg.width, channels).copy()
        if encoding == "rgba8":
            return cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    if encoding == "mono8":
        row = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)
        image = row[:, : msg.width].reshape(msg.height, msg.width).copy()
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    raise ValueError(f"Unsupported image encoding: {msg.encoding}")


def bgr_to_ros_image(image: np.ndarray, frame_id: str, stamp: Any) -> Image:
    """Convert an OpenCV BGR image into a ROS Image message."""
    msg = Image()
    msg.header.stamp = stamp
    msg.header.frame_id = frame_id
    msg.height = int(image.shape[0])
    msg.width = int(image.shape[1])
    msg.encoding = "bgr8"
    msg.is_bigendian = 0
    msg.step = int(msg.width * 3)
    msg.data = image.tobytes()
    return msg


def format_detection_for_topic(detection: dict) -> dict:
    """Expose both the local xywh box and a teammate-friendly xyxy box."""
    x, y, w, h = detection["bbox"]
    return {
        "type": detection["type"],
        "confidence": detection["confidence"],
        "bbox": [x, y, x + w, y + h],
        "bbox_xywh": [x, y, w, h],
        "area_px": detection["area_px"],
    }


class VisionDetectionNode(Node):
    """Run defect detection on images and publish JSON detections."""

    def __init__(self) -> None:
        super().__init__("vision_detection_node")

        self.declare_parameter("use_synthetic", True)
        self.declare_parameter("image_topic", "/zed2i_depth/image_raw")
        self.declare_parameter("detection_topic", "/detections")
        self.declare_parameter("annotated_topic", "/vision/annotated_image")
        self.declare_parameter("synthetic_period_sec", 1.0)
        self.declare_parameter("save_debug_images", True)
        self.declare_parameter("output_dir", "vision_demo/output")
        self.declare_parameter("log_every_n", 5)

        self.use_synthetic = bool(self.get_parameter("use_synthetic").value)
        self.image_topic = str(self.get_parameter("image_topic").value)
        self.detection_topic = str(self.get_parameter("detection_topic").value)
        self.annotated_topic = str(self.get_parameter("annotated_topic").value)
        self.save_debug_images = bool(self.get_parameter("save_debug_images").value)
        self.output_dir = Path(str(self.get_parameter("output_dir").value))
        self.log_every_n = max(1, int(self.get_parameter("log_every_n").value))
        self.frame_count = 0

        self.detection_pub = self.create_publisher(String, self.detection_topic, 10)
        self.annotated_pub = self.create_publisher(Image, self.annotated_topic, 10)

        if self.save_debug_images:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.use_synthetic:
            period = float(self.get_parameter("synthetic_period_sec").value)
            self.timer = self.create_timer(period, self.on_synthetic_timer)
            self.get_logger().info(
                f"Using synthetic tunnel images. Publishing detections on {self.detection_topic}"
            )
        else:
            self.image_sub = self.create_subscription(
                Image,
                self.image_topic,
                self.on_image,
                qos_profile_sensor_data,
            )
            self.get_logger().info(
                f"Subscribing to {self.image_topic}. Publishing detections on {self.detection_topic}"
            )

        self.get_logger().info(f"Annotated images publish on {self.annotated_topic}")

    def on_synthetic_timer(self) -> None:
        stamp = self.get_clock().now().to_msg()
        image = create_synthetic_tunnel()
        self.process_image(image, frame_id="synthetic_tunnel", stamp=stamp, source="synthetic")

    def on_image(self, msg: Image) -> None:
        try:
            image = ros_image_to_bgr(msg)
        except ValueError as exc:
            self.get_logger().warning(str(exc))
            return

        frame_id = msg.header.frame_id or "camera"
        self.process_image(image, frame_id=frame_id, stamp=msg.header.stamp, source=self.image_topic)

    def process_image(self, image: np.ndarray, frame_id: str, stamp: Any, source: str) -> None:
        self.frame_count += 1
        detections = detect_defects(image)
        annotated = draw_detections(image, detections)

        ros_detections = [format_detection_for_topic(item) for item in detections]
        payload = {
            "stamp": {
                "sec": int(stamp.sec),
                "nanosec": int(stamp.nanosec),
            },
            "frame_id": frame_id,
            "source": source,
            "detection_count": len(ros_detections),
            "detections": ros_detections,
        }

        msg = String()
        msg.data = json.dumps(payload, ensure_ascii=False)
        self.detection_pub.publish(msg)
        self.annotated_pub.publish(bgr_to_ros_image(annotated, frame_id, stamp))

        if self.save_debug_images:
            cv2.imwrite(str(self.output_dir / "vision_node_latest_source.png"), image)
            cv2.imwrite(str(self.output_dir / "vision_node_latest_annotated.png"), annotated)
            (self.output_dir / "vision_node_latest_detections.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        if self.frame_count % self.log_every_n == 1:
            self.get_logger().info(
                f"Frame {self.frame_count}: detected {len(ros_detections)} defects from {source}"
            )


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = VisionDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down vision detection node")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
