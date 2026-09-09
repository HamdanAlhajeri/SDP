# Detection and avoidance

This ROS 2 package reads a Hokuyo `sensor_msgs/msg/LaserScan` on `/scan` and
drives the motor and steering servo through the VESC. It moves straight while
the path is clear, slows and steers toward the side with more room when an
obstacle is near, and stops if the obstacle is too close or lidar data stops.

## Before running

Configure and test the VESC as described in
`../jetson_rc_control/jetson/VESC_SETUP.md`. Stop any teleoperation process or
service first: only one process can own `/dev/vesc`.

Start the appropriate ROS 2 Hokuyo driver separately and confirm it publishes:

```bash
ros2 topic echo /scan --once
```

## Build and run

Place this package in a ROS 2 workspace `src` directory, then:

```bash
cd ~/your_ros2_ws
colcon build --packages-select detection_and_avoidance
source install/setup.bash
ros2 launch detection_and_avoidance avoidance.launch.py
```

Alternatively, after starting the Hokuyo driver, use the included runner from
the project root. It builds the package, checks `/scan` and `/dev/vesc`, stops
the teleoperation service while avoidance is running, and restarts it on exit:

```bash
cd ~/SDP
bash detection_and_avoidance/run_avoidance.sh
```

After the first successful build, skip rebuilding with:

```bash
bash detection_and_avoidance/run_avoidance.sh --no-build
```

Keep the driven wheels off the ground on the first run. Press Ctrl+C to stop.
The watchdog also stops and centres the car when scans are missing for 0.5 s.

Tune `config/avoidance.yaml` at low speed. `forward_current` and
`avoid_current` are motor amps; their safe values depend on the car. If steering
turns toward the wrong side, change the signs of both steering direction uses
in `choose_command`, or reverse the steering servo direction in VESC Tool.

The algorithm assumes zero radians in `/scan` points straight forward and
positive angles point left. Verify the lidar orientation before enabling the
motor.
