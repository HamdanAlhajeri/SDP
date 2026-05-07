#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32
import numpy as np


class RacerNode(Node):
    def __init__(self):
        super().__init__('racer_node')

        # --- Tunable parameters ---
        self.lookahead_distance = 1.0   # how far ahead to aim (metres)
        self.max_speed          = 0.5   # throttle at full straight (0-1)
        self.min_speed          = 0.2   # throttle in tight corners (0-1)
        self.max_steering       = 1.0   # steering clamp (-1 to 1)
        self.wall_threshold     = 0.3   # ignore LiDAR returns closer than this (metres)

        # Subscribers
        self.lidar_sub = self.create_subscription(
            LaserScan,
            '/autodrive/roboracer_1/lidar',
            self.lidar_callback,
            10
        )

        # Publishers
        self.throttle_pub = self.create_publisher(Float32, '/autodrive/roboracer_1/throttle_command', 10)
        self.steering_pub = self.create_publisher(Float32, '/autodrive/roboracer_1/steering_command', 10)

        self.get_logger().info('RacerNode started.')

    def lidar_callback(self, msg):
        ranges = np.array(msg.ranges)
        angle_min = msg.angle_min       # start angle of scan (radians)
        angle_inc = msg.angle_increment # radians per index

        # Replace inf/nan with max range
        max_range = msg.range_max
        ranges = np.where(np.isfinite(ranges), ranges, max_range)

        # Mask out returns that are too close (likely noise or car body)
        ranges = np.where(ranges > self.wall_threshold, ranges, max_range)

        # Build angle array for each beam
        num_beams = len(ranges)
        angles = angle_min + np.arange(num_beams) * angle_inc

        # --- Find the best gap ---
        # Split scan into left half and right half relative to forward (angle=0)
        # Forward beam is where angle is closest to 0
        forward_idx = np.argmin(np.abs(angles))

        # Use a window around the front of the car (+/- 135 degrees = full 270 scan)
        left_idx  = 0
        right_idx = num_beams - 1

        # Find the index with the maximum range (furthest free space)
        best_idx = np.argmax(ranges[left_idx:right_idx]) + left_idx
        best_angle = angles[best_idx]

        # --- Compute steering ---
        # Normalise angle to [-1, 1] steering command
        # The scan covers 270 degrees = 1.5*pi radians, so max angle is ~2.36 rad
        max_angle = np.radians(135)  # half of 270
        steering = float(np.clip(best_angle / max_angle, -self.max_steering, self.max_steering))

        # --- Compute throttle ---
        # Slow down proportionally to how much we're steering
        abs_steer = abs(steering)
        throttle = float(self.max_speed - abs_steer * (self.max_speed - self.min_speed))
        throttle = float(np.clip(throttle, self.min_speed, self.max_speed))

        # --- Publish ---
        steer_msg    = Float32()
        throttle_msg = Float32()

        steer_msg.data    = steering
        throttle_msg.data = throttle

        self.steering_pub.publish(steer_msg)
        self.throttle_pub.publish(throttle_msg)

        self.get_logger().info(
            f'best_angle: {np.degrees(best_angle):.1f}° | steering: {steering:.2f} | throttle: {throttle:.2f}',
            throttle_duration_sec=0.5  # only log every 0.5s to avoid spam
        )


def main(args=None):
    rclpy.init(args=args)
    node = RacerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()