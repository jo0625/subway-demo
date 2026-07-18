#!/usr/bin/env python3
"""Drive the Gazebo vehicle forward, then send a reliable stop command."""

import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy


def main() -> int:
    duration = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    speed = float(sys.argv[2]) if len(sys.argv) > 2 else 0.25

    if duration <= 0:
        print("ERROR: duration must be greater than zero.", file=sys.stderr)
        return 2

    rclpy.init(args=None)
    node = rclpy.create_node("subway_drive_forward")
    qos = QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=10,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.VOLATILE,
    )
    publisher = node.create_publisher(Twist, "/cmd_vel", qos)

    print("Waiting for the Gazebo vehicle /cmd_vel subscriber...", flush=True)
    discovery_deadline = time.monotonic() + 20.0
    while publisher.get_subscription_count() < 1:
        if time.monotonic() >= discovery_deadline:
            print(
                "ERROR: No /cmd_vel subscriber was reached. "
                "Start Gazebo first, then run this script again.",
                file=sys.stderr,
            )
            node.destroy_node()
            rclpy.shutdown()
            return 1
        rclpy.spin_once(node, timeout_sec=0.1)

    command = Twist()
    command.linear.x = speed
    stop = Twist()

    print(f"Driving for {duration:g}s at {speed:g} m/s...", flush=True)
    try:
        drive_deadline = time.monotonic() + duration
        while time.monotonic() < drive_deadline:
            publisher.publish(command)
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        # Send several zero commands through the same discovered publisher so
        # stopping does not depend on a second ROS process discovering Gazebo.
        for _ in range(10):
            publisher.publish(stop)
            rclpy.spin_once(node, timeout_sec=0.05)

        print("Vehicle stopped.", flush=True)
        node.destroy_node()
        rclpy.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
