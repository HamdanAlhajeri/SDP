# Jetson RC Car Teleoperation Script

This Python script reads USB gamepad input and generates PWM signals directly from Jetson GPIO pins to control a Traxxas RC car. No Arduino required!

## Prerequisites

### Hardware
- Jetson board (Nano/Xavier/Orin) running Linux
- USB gamepad (Xbox, PlayStation, or generic controller)
- RC car with servo and ESC
- **Wiring:**
  - Servo signal wire → Jetson GPIO Pin 32 (PWM0)
  - ESC signal wire → Jetson GPIO Pin 33 (PWM2)
  - Common ground between RC car battery/ESC and Jetson GND

### Software Dependencies

**Quick Install (Recommended):**

```bash
# Use the provided installation script
chmod +x install_dependencies.sh
./install_dependencies.sh
```

**Or install manually:**

```bash
sudo pip3 install -r requirements.txt
# Or directly:
sudo pip3 install pygame Jetson.GPIO
```

**Note:** Jetson.GPIO requires root privileges, so use `sudo` for installation.

## GPIO Pin Configuration

### Default Pin Assignment (BOARD Numbering)

| Function | GPIO Pin | PWM Channel | Wire Color (typical) |
|----------|----------|-------------|---------------------|
| Steering | Pin 32   | PWM0        | White/Yellow        |
| Throttle | Pin 33   | PWM2        | White/Yellow        |
| Ground   | Pin 6/14/20/30/34/39 | GND | Brown/Black |

**Pin Layout Reference (Jetson Nano 40-pin header):**
```
         3V3  (1) (2)  5V
       GPIO2  (3) (4)  5V
       GPIO3  (5) (6)  GND
       GPIO4  (7) (8)  GPIO14
         GND  (9) (10) GPIO15
      GPIO17 (11) (12) GPIO18
      GPIO27 (13) (14) GND
      GPIO22 (15) (16) GPIO23
         3V3 (17) (18) GPIO24
      GPIO10 (19) (20) GND
       GPIO9 (21) (22) GPIO25
      GPIO11 (23) (24) GPIO8
         GND (25) (26) GPIO7
        ...
   PWM0/GPIO13 (32) (33) GPIO19/PWM2  ← Use these!
         GPIO6 (34) (35) GPIO26
      GPIO16  (36) (37) GPIO20
         GND (38) (39) GPIO21
```

### Wiring Instructions

1. **Locate the servo connector** (3-wire):
   - Signal (usually white/yellow/orange)
   - Power (usually red) - DO NOT connect to Jetson!
   - Ground (usually brown/black)

2. **Connect steering servo:**
   - Signal wire → Jetson Pin 32
   - Ground wire → Jetson GND (Pin 34 recommended, close to PWM pins)
   - Power wire → ESC BEC or external 5-6V power supply

3. **Connect ESC:**
   - Signal wire → Jetson Pin 33
   - Ground wire → Same ground as servo (shared ground)
   - Power wires → RC car battery (as normal)

4. **Important safety notes:**
   - Never connect servo/ESC power (red wire) to Jetson 3.3V or 5V pins
   - Always connect grounds together (Jetson GND + ESC/servo GND)
   - 3.3V signal from Jetson is sufficient for most RC servos/ESCs
   - Double-check polarity before powering on

## Setup Instructions

### Step 1: Install Dependencies

**Using installation script (recommended):**

```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

This script will:
- Install `pygame` and `Jetson.GPIO` from requirements.txt
- Verify GPIO permissions

**Manual installation:**

```bash
# Update pip
sudo pip3 install --upgrade pip

# Install from requirements file
sudo pip3 install -r requirements.txt

# Or install packages directly
sudo pip3 install pygame Jetson.GPIO

# Verify installation
python3 -c "import pygame, Jetson.GPIO; print('Dependencies OK')"
```

### Step 2: Connect Hardware

1. **Connect servo signal wires to Jetson GPIO:**
   - Steering servo signal → Pin 32
   - ESC signal → Pin 33
   - Both grounds → Common Jetson GND pin (Pin 34 recommended)
   
2. **Power connections:**
   - Servo power (red wire) → ESC BEC or external 5-6V supply
   - ESC power → RC car battery (as normal)
   - **Never connect servo/ESC power to Jetson pins!**

3. **Connect USB gamepad** to Jetson

4. **Verify gamepad connection:**
   ```bash
   ls /dev/input/js*  # Should show joystick device
   ```

### Step 3: Test the Script

**Important:** The script requires root privileges to access GPIO pins.

```bash
cd ~/Desktop/SDP/jetson_rc_control/jetson
sudo python3 teleop_rc.py
```

Expected output:
```
Initializing pygame...
Found joystick: Xbox Wireless Controller
  Axes: 6
  Buttons: 11

Initializing GPIO pins...
  Steering: Pin 32
  Throttle: Pin 33
GPIO PWM initialized!

============================================================
RC CAR TELEOPERATION ACTIVE
============================================================
Controls:
  Left Stick X-axis: Steering
  Left Stick Y-axis: Throttle (forward/reverse)
  Press Ctrl+C to exit safely
============================================================

Steer: 1500µs (+0.00)  |  Throttle: 1500µs (+0.00)
```

## Usage

### Basic Usage

```bash
sudo python3 teleop_rc.py
```

### With Custom GPIO Pins

```bash
sudo python3 teleop_rc.py --steer-pin 32 --throttle-pin 33
```

### With Custom Deadzone

```bash
sudo python3 teleop_rc.py --deadzone 0.15
```

### Combined Options

```bash
sudo python3 teleop_rc.py --steer-pin 32 --throttle-pin 33 --deadzone 0.2
```

### View All Options

```bash
sudo python3 teleop_rc.py --help
```

## Configuration Constants

Edit [teleop_rc.py](teleop_rc.py) to customize behavior:

| Constant | Default Value | Description |
|----------|---------------|-------------|
| `STEER_PIN` | `32` | GPIO pin for steering (BOARD numbering) |
| `THROTTLE_PIN` | `33` | GPIO pin for throttle (BOARD numbering) |
| `PWM_FREQ_HZ` | `50` | PWM frequency (Hz) |
| `LOOP_HZ` | `50` | Control loop frequency |
| `STEER_AXIS` | `0` | Joystick axis for steering (X) |
| `THROTTLE_AXIS` | `1` | Joystick axis for throttle (Y) |
| `DEADZONE` | `0.1` | Joystick deadzone threshold |
| `DEBUG_PRINT_HZ` | `5` | Debug output frequency |

## Troubleshooting

### Error: "Jetson.GPIO is not installed"

**Solution:**
```bash
sudo pip3 install Jetson.GPIO
```

### Error: "GPIO access denied" or Permission Issues

**Cause:** Script not run with root privileges.

**Solution:**
```bash
sudo python3 teleop_rc.py
```

### Error: "No joystick/gamepad found!"

**Cause:** USB gamepad not detected.

**Solutions:**
```bash
# Check if gamepad is connected
ls /dev/input/js*

# If not shown, try:
sudo apt-get install joystick
jstest /dev/input/js0  # Test gamepad input
```

### Servo/ESC Not Responding

**Possible causes:**

1. **Wrong pin connections** - Double-check Pin 32 and 33
2. **No common ground** - Must share ground between Jetson and RC electronics
3. **Servo power issue** - Ensure servo has external 5-6V power supply
4. **PWM signal level** - Most servos work with 3.3V, but some older ones may require 5V level shifter

**Debugging steps:**
```bash
# Check if PWM devices are available
ls /sys/class/pwm/
```

### Wrong Joystick Axes

**Symptoms:** Steering controls throttle or vice versa.

**Solution:** Find correct axis indices:

```bash
# Install jstest utility
sudo apt-get install joystick

# Test gamepad
jstest /dev/input/js0

# Move left stick and note which axis numbers change
# Edit teleop_rc.py to match your controller
```

Example axes for different controllers:
- **Xbox Controller:** Axis 0 (left X), Axis 1 (left Y)
- **PlayStation Controller:** Axis 0 (left X), Axis 1 (left Y)
- **Generic USB:** May vary - use jstest to verify

### Inverted Controls

**Symptoms:** Forward is backward, or left is right.

**Solutions:**

For inverted throttle, edit the control loop section:
```python
# Current (inverts Y-axis):
throttle_raw = -joystick.get_axis(THROTTLE_AXIS)

# Remove negative sign if already inverted:
throttle_raw = joystick.get_axis(THROTTLE_AXIS)
```

For inverted steering, modify the `axis_to_us()` function:
```python
def axis_to_us(x: float) -> int:
    x = max(-1.0, min(1.0, x))
    return int(NEUTRAL_US - 500 * x)  # Note: minus instead of plus
```

## PWM Signal Details

### Technical Specifications

- **Frequency:** 50 Hz (20ms period)
- **Pulse Width Range:** 1000-2000 microseconds
- **Neutral Position:** 1500 microseconds
- **Signal Level:** 3.3V (Jetson GPIO output)

### PWM Value Ranges

| Pulse Width | Steering Position | Throttle Action |
|-------------|-------------------|-----------------|
| 1000µs      | Full left         | Full reverse    |
| 1500µs      | Center (neutral)  | Stopped         |
| 2000µs      | Full right        | Full forward    |

### Duty Cycle Calculation

At 50Hz (20ms = 20,000µs period):
- 1000µs = 5.0% duty cycle
- 1500µs = 7.5% duty cycle (neutral)
- 2000µs = 10.0% duty cycle

## Safety Features

1. **Emergency Stop:** Press Ctrl+C to immediately set neutral position (1500µs) on both channels
2. **Deadzone:** Small joystick movements (< 0.1 by default) are ignored to prevent drift
3. **Input Clamping:** All values are clamped to safe range [1000, 2000]µs
4. **GPIO Cleanup:** Proper GPIO cleanup on exit to prevent pin conflicts

## Advanced Configuration

### Changing Control Loop Frequency

Higher frequency = smoother control but more CPU usage:
```python
LOOP_HZ = 100  # 100 Hz updates
```

### Adjusting Debug Output

Show more/less frequent updates:
```python
DEBUG_PRINT_HZ = 10  # 10 updates per second
DEBUG_PRINT_HZ = 1   # 1 update per second (less spam)
```

### Using Different Joystick

If you have multiple gamepads connected:
```python
joystick = pygame.joystick.Joystick(0)  # First gamepad
joystick = pygame.joystick.Joystick(1)  # Second gamepad
```

### Using Different GPIO Pins

Check Jetson pinout and select PWM-capable pins. Common options:
- **Jetson Nano:** Pin 32 (PWM0), Pin 33 (PWM2)
- **Jetson Xavier NX:** Multiple PWM channels available
- **Jetson Orin:** Multiple PWM channels available

## Making Script Executable

```bash
# Make script executable
chmod +x teleop_rc.py

# Run directly (still needs sudo)
sudo ./teleop_rc.py
```

## Running on Boot (Optional)

Create a systemd service to auto-start (note: requires root privileges):

```bash
sudo nano /etc/systemd/system/rc-teleop.service
```

Add:
```ini
[Unit]
Description=RC Car Teleoperation via GPIO
After=multi-user.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/YOUR_USERNAME/Desktop/SDP/jetson_rc_control/jetson
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/Desktop/SDP/jetson_rc_control/jetson/teleop_rc.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Note:** Service must run as root for GPIO access.

Enable and start:
```bash
sudo systemctl enable rc-teleop.service
sudo systemctl start rc-teleop.service
sudo systemctl status rc-teleop.service
```

## Additional Resources

- [Main Project README](../README.md)
- [pygame Documentation](https://www.pygame.org/docs/)
- [Jetson.GPIO Documentation](https://github.com/NVIDIA/jetson-gpio)
- [Jetson GPIO Pinout Reference](https://jetsonhacks.com/nvidia-jetson-nano-j41-header-pinout/)

