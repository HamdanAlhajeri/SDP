"""ROS 2 node for simple, conservative reactive obstacle avoidance."""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

from .planner import choose_command, sector_distance
from .vesc_driver import DEFAULT_PORT, VESC


class AvoidObstacles(Node):
    def __init__(self):
        super().__init__('avoid_obstacles')
        self.declare_parameter('scan_topic', '/scan')
        self.declare_parameter('vesc_port', DEFAULT_PORT)
        self.declare_parameter('front_half_angle_deg', 20.0)
        self.declare_parameter('side_angle_deg', 65.0)
        self.declare_parameter('stop_distance', 0.75)
        self.declare_parameter('clear_distance', 1.8)
        self.declare_parameter('forward_current', 8.0)
        self.declare_parameter('avoid_current', 4.0)
        self.declare_parameter('steer_range', 0.25)
        self.declare_parameter('scan_timeout', 0.5)

        stop = self.get_parameter('stop_distance').value
        clear = self.get_parameter('clear_distance').value
        if stop <= 0.0 or clear <= stop:
            raise ValueError('Require 0 < stop_distance < clear_distance')

        port = self.get_parameter('vesc_port').value
        self.vesc = VESC(port)
        self.vesc.stop()
        self.last_scan_time = None
        self.last_state = None

        topic = self.get_parameter('scan_topic').value
        self.subscription = self.create_subscription(
            LaserScan, topic, self.scan_callback, qos_profile_sensor_data)
        self.watchdog = self.create_timer(0.1, self.watchdog_callback)
        self.get_logger().info(
            'Avoidance armed: listening on %s, VESC %s' % (topic, port))

    def scan_callback(self, scan):
        front_half = math.radians(
            self.get_parameter('front_half_angle_deg').value)
        side_angle = math.radians(self.get_parameter('side_angle_deg').value)
        front = sector_distance(scan, -front_half, front_half)
        left = sector_distance(scan, front_half, side_angle)
        right = sector_distance(scan, -side_angle, -front_half)

        if not math.isfinite(front):
            self.vesc.stop()
            self._log_state('no_valid_front_scan', front, left, right)
            self.last_scan_time = self.get_clock().now()
            return

        servo, current, state = choose_command(
            front, left, right,
            self.get_parameter('stop_distance').value,
            self.get_parameter('clear_distance').value,
            self.get_parameter('steer_range').value,
            self.get_parameter('forward_current').value,
            self.get_parameter('avoid_current').value)
        self.vesc.set_servo_pos(servo)
        self.vesc.set_current(current)
        self.last_scan_time = self.get_clock().now()
        self._log_state(state, front, left, right)

    def _log_state(self, state, front, left, right):
        if state != self.last_state:
            self.get_logger().info(
                '%s: front=%.2f m left=%.2f m right=%.2f m' %
                (state, front, left, right))
            self.last_state = state

    def watchdog_callback(self):
        timeout = self.get_parameter('scan_timeout').value
        if (self.last_scan_time is None or
                (self.get_clock().now() - self.last_scan_time).nanoseconds /
                1e9 > timeout):
            self.vesc.stop()
            if self.last_state != 'scan_timeout':
                self.get_logger().warning('No recent lidar scan; car stopped')
                self.last_state = 'scan_timeout'

    def destroy_node(self):
        self.vesc.close()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = AvoidObstacles()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
