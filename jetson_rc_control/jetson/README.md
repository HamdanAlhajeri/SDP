# Jetson RC Car Teleoperation Script

This Python script reads USB gamepad input and sends PWM commands to an Arduino via serial connection to control a Traxxas RC car.

## Prerequisites

### Hardware
- Jetson board (Nano/Xavier/Orin) running Linux
- USB gamepad (Xbox, PlayStation, or generic controller)
- Arduino Uno/Nano connected via USB cable
- RC car with servo and ESC connected to Arduino

### Software Dependencies

**Quick Install (Recommended):**

```bash
# Use the provided installation script
chmod +x install_dependencies.sh
./install_dependencies.sh
```

**Or install manually:**

```bash
pip3 install -r requirements.txt
# Or directly:
pip3 install pygame pyserial
```

## Serial Port Configuration

### Understanding Serial Ports

The script communicates with the Arduino through a serial port. On Linux systems, USB-connected Arduinos typically appear as:

- **`/dev/ttyACM0`** - Most Arduino Uno/Nano boards (default in script)
- **`/dev/ttyUSB0`** - Some Arduino clones with CH340/CP2102 USB chips
- **`/dev/ttyACM1`**, **`/dev/ttyUSB1`**, etc. - If multiple devices are connected

### Finding Your Arduino Port

#### Method 1: List All USB Serial Devices

```bash
# Before connecting Arduino
ls /dev/tty*

# After connecting Arduino
ls /dev/tty*

# Look for new ttyACM* or ttyUSB* device
```

#### Method 2: Using dmesg

```bash
# Connect Arduino and immediately run:
dmesg | tail

# Look for lines like:
# [  123.456] cdc_acm 1-3:1.0: ttyACM0: USB ACM device
# [  123.456] ch341 1-3:1.0: ch341-uart converter now attached to ttyUSB0
```

#### Method 3: Quick Check

```bash
# List Arduino-specific ports
ls /dev/ttyACM*  # For standard Arduino
ls /dev/ttyUSB*  # For clone boards
```

### Setting the Serial Port

#### Option 1: Default Port (Edit Script)

Edit [teleop_rc.py](teleop_rc.py) line 29:

```python
SERIAL_PORT = "/dev/ttyACM0"  # Change this to your port
```

Common alternatives:
```python
SERIAL_PORT = "/dev/ttyUSB0"   # For CH340 Arduino clones
SERIAL_PORT = "/dev/ttyACM1"   # If multiple Arduinos connected
```

#### Option 2: Command Line Argument (Recommended)

```bash
# Use --port flag to override default
python3 teleop_rc.py --port /dev/ttyUSB0
```

This method doesn't require editing the script.

## Setup Instructions

### Step 1: Install Dependencies

**Using installation script (recommended):**

```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

This script will:
- Remove conflicting `serial` package
- Install `pygame` and `pyserial` from requirements.txt
- Add your user to the `dialout` group for serial permissions

**Manual installation:**

```bash
# Update pip
pip3 install --upgrade pip

# Install from requirements file
pip3 install -r requirements.txt

# Or install packages directly
pip3 install pygame pyserial

# Verify installation
python3 -c "import pygame, serial; print('Dependencies OK')"
```

### Step 2: Set Serial Permissions

By default, serial ports require root access. Add your user to the `dialout` group:

```bash
# Add current user to dialout group
sudo usermod -aG dialout $USER

# Verify group membership
groups $USER

# IMPORTANT: Log out and log back in for changes to take effect
```

Alternative (temporary, requires password each time):
```bash
sudo chmod 666 /dev/ttyACM0  # Replace with your port
```

### Step 3: Connect Hardware

1. **Connect Arduino to Jetson** via USB cable
2. **Verify Arduino connection:**
   ```bash
   ls -l /dev/ttyACM0  # Should show the device
   ```
3. **Upload Arduino firmware** ([arduino/rc_bridge.ino](../arduino/rc_bridge.ino))
4. **Connect USB gamepad** to Jetson
5. **Verify gamepad connection:**
   ```bash
   ls /dev/input/js*  # Should show joystick device
   ```

### Step 4: Test the Script

```bash
cd ~/Desktop/SDP/jetson
python3 teleop_rc.py
```

Expected output:
```
Initializing pygame...
Found joystick: Xbox Wireless Controller
  Axes: 6
  Buttons: 11
Connecting to Arduino on /dev/ttyACM0 at 115200 baud...
Serial connection established!

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
python3 teleop_rc.py
```

### With Custom Port

```bash
python3 teleop_rc.py --port /dev/ttyUSB0
```

### With Custom Baud Rate

```bash
python3 teleop_rc.py --baud 9600
```

### With Custom Deadzone

```bash
python3 teleop_rc.py --deadzone 0.15
```

### Combined Options

```bash
python3 teleop_rc.py --port /dev/ttyUSB0 --baud 115200 --deadzone 0.1
```

### View All Options

```bash
python3 teleop_rc.py --help
```

## Configuration Constants

Edit [teleop_rc.py](teleop_rc.py) to customize behavior:

| Constant | Line | Default Value | Description |
|----------|------|---------------|-------------|
| `SERIAL_PORT` | 29 | `/dev/ttyACM0` | Arduino serial port |
| `BAUD_RATE` | 30 | `115200` | Serial communication speed |
| `LOOP_HZ` | 31 | `50` | Control loop frequency |
| `STEER_AXIS` | 34 | `0` | Joystick axis for steering (X) |
| `THROTTLE_AXIS` | 35 | `1` | Joystick axis for throttle (Y) |
| `DEADZONE` | 38 | `0.1` | Joystick deadzone threshold |
| `DEBUG_PRINT_HZ` | 45 | `5` | Debug output frequency |

## Troubleshooting

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

### Error: "Failed to open serial port"

**Cause:** Arduino not connected or permission denied.

**Solutions:**

1. **Verify Arduino is connected:**
   ```bash
   ls -l /dev/ttyACM*
   ls -l /dev/ttyUSB*
   ```

2. **Check permissions:**
   ```bash
   # Should show: crw-rw---- 1 root dialout
   ls -l /dev/ttyACM0
   
   # Add yourself to dialout group
   sudo usermod -aG dialout $USER
   # Then log out and back in
   ```

3. **Try different port:**
   ```bash
   python3 teleop_rc.py --port /dev/ttyUSB0
   ```

4. **Check if another program is using the port:**
   ```bash
   # Close Arduino IDE Serial Monitor
   # Stop any other programs accessing the port
   lsof /dev/ttyACM0
   ```

### Error: "Permission denied"

**Cause:** User not in `dialout` group.

**Solution:**
```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Verify
groups $USER

# MUST log out and back in for changes to take effect
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
# Edit teleop_rc.py lines 34-35 with correct numbers
```

Example axes for different controllers:
- **Xbox Controller:** Axis 0 (left X), Axis 1 (left Y)
- **PlayStation Controller:** Axis 0 (left X), Axis 1 (left Y)
- **Generic USB:** May vary - use jstest to verify

### Inverted Controls

**Symptoms:** Forward is backward, or left is right.

**Solutions:**

For inverted throttle, edit line 175:
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

## Serial Communication Protocol

The script sends commands in the format:
```
S<steering_us> T<throttle_us>\n
```

### Example Commands

| Command | Steering | Throttle | Result |
|---------|----------|----------|--------|
| `S1500 T1500\n` | Neutral (1500µs) | Neutral (1500µs) | Centered, stopped |
| `S1000 T1500\n` | Full left (1000µs) | Neutral | Sharp left, no motion |
| `S2000 T1500\n` | Full right (2000µs) | Neutral | Sharp right, no motion |
| `S1500 T2000\n` | Neutral | Full forward (2000µs) | Straight line forward |
| `S1500 T1000\n` | Neutral | Full reverse (1000µs) | Straight line backward |
| `S1800 T1700\n` | Right (1800µs) | Forward (1700µs) | Turn right while moving |

### PWM Value Ranges

- **1000µs:** Full left / full reverse
- **1500µs:** Center / neutral (default)
- **2000µs:** Full right / full forward

## Safety Features

1. **Emergency Stop:** Press Ctrl+C to immediately send neutral command (1500µs) to both steering and throttle
2. **Deadzone:** Small joystick movements (< 0.1 by default) are ignored to prevent drift
3. **Input Clamping:** All values are clamped to safe range [1000, 2000]µs before sending

## Advanced Configuration

### Changing Control Loop Frequency

Higher frequency = smoother control but more CPU usage:
```python
LOOP_HZ = 100  # 100 Hz updates (line 31)
```

### Adjusting Debug Output

Show more/less frequent updates:
```python
DEBUG_PRINT_HZ = 10  # 10 updates per second (line 45)
DEBUG_PRINT_HZ = 1   # 1 update per second (less spam)
```

### Using Different Joystick

If you have multiple gamepads, change line 128:
```python
joystick = pygame.joystick.Joystick(0)  # First gamepad
joystick = pygame.joystick.Joystick(1)  # Second gamepad
```

## Making Script Executable

```bash
# Make script executable
chmod +x teleop_rc.py

# Run directly
./teleop_rc.py --port /dev/ttyACM0
```

## Running on Boot (Optional)

Create a systemd service to auto-start:

```bash
sudo nano /etc/systemd/system/rc-teleop.service
```

Add:
```ini
[Unit]
Description=RC Car Teleoperation
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/Desktop/SDP/jetson
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/Desktop/SDP/jetson/teleop_rc.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable rc-teleop.service
sudo systemctl start rc-teleop.service
sudo systemctl status rc-teleop.service
```

## Additional Resources

- [Main Project README](../README.md)
- [Arduino Firmware](../arduino/rc_bridge.ino)
- [pygame Documentation](https://www.pygame.org/docs/)
- [pySerial Documentation](https://pyserial.readthedocs.io/)
