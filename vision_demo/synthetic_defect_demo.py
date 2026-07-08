#!/usr/bin/env python3
"""Small OpenCV demo for subway tunnel defect detection.

The demo intentionally uses deterministic synthetic data and simple rules so the
vision branch has something visible before YOLO training data is ready.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


CLASS_COLORS = {
    "crack": (30, 30, 255),
    "leakage": (255, 170, 30),
    "loose_bracket": (40, 180, 255),
}


def create_synthetic_tunnel(width: int = 1280, height: int = 720) -> np.ndarray:
    """Create a simple tunnel scene with three visual defects."""
    image = np.full((height, width, 3), (42, 43, 45), dtype=np.uint8)

    # Tunnel structure.
    cv2.rectangle(image, (0, 0), (width, height), (38, 39, 41), -1)
    cv2.fillPoly(
        image,
        [np.array([(0, 0), (390, 85), (455, 610), (0, height)], dtype=np.int32)],
        (72, 73, 73),
    )
    cv2.fillPoly(
        image,
        [np.array([(width, 0), (890, 85), (825, 610), (width, height)], dtype=np.int32)],
        (74, 74, 72),
    )
    cv2.fillPoly(
        image,
        [np.array([(390, 85), (890, 85), (825, 610), (455, 610)], dtype=np.int32)],
        (54, 55, 56),
    )
    cv2.fillPoly(
        image,
        [np.array([(0, height), (455, 610), (825, 610), (width, height)], dtype=np.int32)],
        (48, 48, 47),
    )

    # Rails and sleepers.
    cv2.line(image, (500, height), (595, 520), (105, 105, 100), 5, cv2.LINE_AA)
    cv2.line(image, (780, height), (690, 520), (105, 105, 100), 5, cv2.LINE_AA)
    for y in range(535, 710, 28):
        scale = (y - 520) / 200
        left = int(555 - 90 * scale)
        right = int(725 + 90 * scale)
        cv2.line(image, (left, y), (right, y), (82, 82, 80), 4, cv2.LINE_AA)

    # Tunnel lights.
    for x in (360, 640, 920):
        cv2.ellipse(image, (x, 110), (42, 12), 0, 0, 360, (165, 165, 132), -1)
        cv2.ellipse(image, (x, 110), (68, 24), 0, 0, 360, (80, 80, 65), 2)

    # Defect 1: crack on the left wall.
    crack = np.array([(245, 170), (226, 235), (256, 300), (232, 370), (248, 445)], dtype=np.int32)
    cv2.polylines(image, [crack], False, (8, 8, 8), 7, cv2.LINE_AA)
    cv2.line(image, (236, 260), (195, 300), (8, 8, 8), 4, cv2.LINE_AA)
    cv2.line(image, (244, 350), (285, 390), (8, 8, 8), 4, cv2.LINE_AA)

    # Defect 2: water leakage on the right wall.
    leak = np.array(
        [(1010, 225), (1060, 245), (1085, 320), (1042, 392), (972, 370), (948, 290)],
        dtype=np.int32,
    )
    overlay = image.copy()
    cv2.fillPoly(overlay, [leak], (210, 135, 35))
    image = cv2.addWeighted(overlay, 0.65, image, 0.35, 0)
    for x, y, length in ((1005, 390, 70), (1058, 380, 48), (980, 365, 38)):
        cv2.line(image, (x, y), (x - 8, y + length), (220, 160, 55), 4, cv2.LINE_AA)

    # Defect 3: loose bracket marker.
    rect = ((865, 205), (118, 28), -12)
    box = cv2.boxPoints(rect).astype(np.int32)
    cv2.fillPoly(image, [box], (20, 120, 235))
    cv2.circle(image, (820, 212), 10, (30, 30, 35), -1)
    cv2.circle(image, (907, 194), 10, (30, 30, 35), -1)

    noise = np.random.default_rng(7).normal(0, 4, image.shape).astype(np.int16)
    noisy = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return noisy


def contour_detections(
    mask: np.ndarray,
    defect_type: str,
    min_area: float,
    confidence_base: float,
) -> list[dict]:
    detections: list[dict] = []
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        confidence = min(0.98, confidence_base + area / 10000.0)
        detections.append(
            {
                "type": defect_type,
                "confidence": round(confidence, 3),
                "bbox": [int(x), int(y), int(w), int(h)],
                "area_px": round(area, 1),
            }
        )

    return detections


def detect_defects(image: np.ndarray) -> list[dict]:
    """Detect synthetic crack, leakage, and loose bracket defects."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Dark, thin, vertical-ish marks on the wall are treated as cracks.
    crack_mask = cv2.inRange(gray, 0, 32)
    crack_mask[:110, :] = 0
    crack_mask[560:, :] = 0
    crack_mask[:, :110] = 0
    crack_mask[:, 360:] = 0
    crack_mask = cv2.dilate(crack_mask, np.ones((5, 5), np.uint8), iterations=1)

    crack_detections = []
    for item in contour_detections(crack_mask, "crack", min_area=180, confidence_base=0.72):
        _, _, w, h = item["bbox"]
        if h >= 45 and h / max(w, 1) >= 1.1:
            crack_detections.append(item)

    # Blue/cyan regions are treated as leakage.
    leakage_mask = cv2.inRange(hsv, np.array([88, 80, 55]), np.array([118, 255, 255]))
    leakage_mask[:150, :] = 0
    leakage_mask[530:, :] = 0
    leakage_mask[:, :850] = 0
    leakage_mask = cv2.morphologyEx(leakage_mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    leakage_detections = contour_detections(leakage_mask, "leakage", min_area=700, confidence_base=0.78)

    # Orange regions are treated as loose brackets.
    bracket_mask = cv2.inRange(hsv, np.array([5, 90, 80]), np.array([24, 255, 255]))
    bracket_mask = cv2.morphologyEx(bracket_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    bracket_detections = contour_detections(
        bracket_mask,
        "loose_bracket",
        min_area=250,
        confidence_base=0.74,
    )

    detections = crack_detections + leakage_detections + bracket_detections
    return sorted(detections, key=lambda item: item["bbox"][0])


def draw_detections(image: np.ndarray, detections: Iterable[dict]) -> np.ndarray:
    annotated = image.copy()

    for detection in detections:
        x, y, w, h = detection["bbox"]
        defect_type = detection["type"]
        color = CLASS_COLORS.get(defect_type, (0, 255, 255))
        label = f"{defect_type} {detection['confidence']:.2f}"

        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        label_w, label_h = label_size
        label_y = max(24, y)
        cv2.rectangle(annotated, (x, label_y - label_h - 10), (x + label_w + 8, label_y + 4), color, -1)
        cv2.putText(
            annotated,
            label,
            (x + 4, label_y - 4),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (20, 20, 20),
            2,
            cv2.LINE_AA,
        )

    return annotated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a simple subway tunnel vision defect demo.")
    parser.add_argument("--image", type=Path, help="Optional input image. If omitted, a synthetic image is generated.")
    parser.add_argument("--output-dir", type=Path, default=Path("vision_demo/output"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.image:
        image = cv2.imread(str(args.image))
        if image is None:
            raise SystemExit(f"Could not read image: {args.image}")
        stem = args.image.stem
        source_path = output_dir / f"{stem}_source.png"
    else:
        image = create_synthetic_tunnel()
        stem = "synthetic_tunnel"
        source_path = output_dir / "synthetic_tunnel.png"

    detections = detect_defects(image)
    annotated = draw_detections(image, detections)

    annotated_path = output_dir / f"{stem}_annotated.png"
    json_path = output_dir / "detections.json"

    cv2.imwrite(str(source_path), image)
    cv2.imwrite(str(annotated_path), annotated)
    json_path.write_text(
        json.dumps(
            {
                "image_id": source_path.name,
                "detection_count": len(detections),
                "detections": detections,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Wrote source image: {source_path}")
    print(f"Wrote annotated image: {annotated_path}")
    print(f"Wrote detections: {json_path}")
    print(f"Detected {len(detections)} defects")


if __name__ == "__main__":
    main()
