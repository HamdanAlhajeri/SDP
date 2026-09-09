"""Pure scan-processing and command-selection functions."""

import math
import statistics


SERVO_CENTER = 0.5


def clamp(value, low, high):
    return max(low, min(high, value))


def ramp_current(commanded, target, elapsed, launch_current, ramp_rate):
    """Ramp current increases while applying reductions immediately."""
    if target <= 0.0:
        return 0.0
    if commanded <= 0.0:
        return min(target, launch_current)
    if target <= commanded:
        return target
    return min(target, commanded + ramp_rate * max(0.0, elapsed))


def sector_distance(scan, start_angle, end_angle):
    """Return a robust near distance for a scan angle sector, in metres."""
    samples = []
    for index, distance in enumerate(scan.ranges):
        angle = scan.angle_min + index * scan.angle_increment
        if (start_angle <= angle <= end_angle and math.isfinite(distance)
                and scan.range_min <= distance <= scan.range_max):
            samples.append(float(distance))
    if not samples:
        return math.inf
    # Median of the nearest 20% rejects isolated bad returns without hiding
    # an obstacle that occupies a meaningful part of the car's path.
    samples.sort()
    near_count = max(1, int(math.ceil(len(samples) * 0.20)))
    return statistics.median(samples[:near_count])


def choose_command(front, left, right, stop_distance, clear_distance,
                   steer_range, forward_current, avoid_current):
    """Calculate (servo position, motor current, state)."""
    if front <= stop_distance:
        direction = 1.0 if left >= right else -1.0
        return (SERVO_CENTER + direction * steer_range, 0.0, 'blocked')
    if front < clear_distance:
        direction = 1.0 if left >= right else -1.0
        proximity = ((clear_distance - front) /
                     (clear_distance - stop_distance))
        steering = direction * steer_range * clamp(proximity, 0.35, 1.0)
        return (SERVO_CENTER + steering, avoid_current, 'avoiding')
    balance = clamp((left - right) / max(clear_distance, 0.01), -1.0, 1.0)
    return (SERVO_CENTER + 0.25 * steer_range * balance,
            forward_current, 'clear')
