import math
from types import SimpleNamespace

from detection_and_avoidance.planner import (
    choose_command, ramp_current, sector_distance)


def test_clear_path_drives_forward():
    servo, current, state = choose_command(
        3.0, 2.0, 2.0, 0.75, 1.8, 0.25, 8.0, 4.0)
    assert servo == 0.5
    assert current == 8.0
    assert state == 'clear'


def test_obstacle_steers_toward_clearer_left_side():
    servo, current, state = choose_command(
        1.0, 2.5, 0.8, 0.75, 1.8, 0.25, 8.0, 4.0)
    assert servo > 0.5
    assert current == 4.0
    assert state == 'avoiding'


def test_close_obstacle_stops():
    _, current, state = choose_command(
        0.5, 2.0, 1.0, 0.75, 1.8, 0.25, 8.0, 4.0)
    assert current == 0.0
    assert state == 'blocked'


def test_sector_ignores_invalid_ranges():
    scan = SimpleNamespace(
        angle_min=-math.pi / 2,
        angle_increment=math.pi / 4,
        range_min=0.1,
        range_max=10.0,
        ranges=[math.inf, 1.0, math.nan, 2.0, 3.0])
    assert sector_distance(scan, -math.pi / 2, 0.0) == 1.0


def test_current_starts_at_launch_level_then_ramps():
    assert ramp_current(0.0, 80.0, 0.02, 5.0, 22.0) == 5.0
    assert ramp_current(5.0, 80.0, 1.0, 5.0, 22.0) == 27.0


def test_current_reduction_and_stop_are_immediate():
    assert ramp_current(80.0, 40.0, 0.02, 5.0, 22.0) == 40.0
    assert ramp_current(40.0, 0.0, 0.02, 5.0, 22.0) == 0.0
