# Jetson-to-RC Car Control System

Direct GPIO control system for controlling a Traxxas RC car using a Jetson board and USB gamepad teleoperation. **No Arduino required!**

> **Module:** This is a standalone control module within the larger SDP robotics project. It can be used independently or integrated into autonomous vehicle systems.

## System Overview

**Data Flow:**
```
USB Gamepad → Jetson (Python + GPIO PWM) → RC Car (Servo + ESC)
```

The Jetson generates 50Hz PWM signals directly from its GPIO pins to control the steering servo and ESC, eliminating the need for an Arduino middleman.

## Hardware Requirements

- **Jetson Board** (Nano/Xavier/Orin with Linux + Python 3)
- **USB Gamepad** (Xbox/PlayStation/Generic)
- **Traxxas RC Car** with:
  - 1× Steering servo
  - 1× ESC (Electronic Speed Controller)
- **5-6V Power Supply** for servo (ESC BEC or external regulator)

### Wiring Connections

#### Jetson GPIO Pin Connections

**Direct PWM Control via GPIO**

The Jetson generates PWM signals directly from GPIO pins - no Arduino needed:

| Jetson Component | Connection | Notes |
|------------------|------------|-------|
| **Pin 32 (PWM0)** | Steering servo signal | 3.3V PWM signal output |
| **Pin 33 (PWM2)** | ESC signal | 3.3V PWM signal output |
| **Pin 34 (GND)** | Common ground | Shared with servo/ESC |
| **DC Power Input** | 5V Barrel Jack or USB-C | Powers the Jetson board |

**Jetson Nano 40-Pin Header (simplified):**
```
         3V3  (1) (2)  5V
       GPIO2  (3) (4)  5V
       GPIO3  (5) (6)  GND
       GPIO4  (7) (8)  GPIO14
         GND  (9) (10) GPIO15
         ... ... ...
   PWM0/GPIO13 (32) (33) GPIO19/PWM2  ← Signal pins for servo/ESC
      GPIO6 (34) (35) GPIO26
         ... ... ...
```

#### RC Car Wiring

| Component | Connection | Jetson Pin / Notes |
|-----------|------------|-------------------|
| Steering Servo Signal Wire | → | Jetson Pin 32 (PWM0) |
| ESC Signal Wire | → | Jetson Pin 33 (PWM2) |
| Common Ground | → | Jetson Pin 34 (GND) |
| Servo Power (5V) | ← | ESC BEC or external 5-6V supply |

#### Detailed Wiring Guide

**1. Steering Servo (3 wires)**

Standard servo wire colors:
- **Orange/Yellow/White** = Signal wire → Connect to Jetson **Pin 32**
- **Red** = Power (5V) → Connect to ESC BEC 5V output OR external 5V regulator
- **Brown/Black** = Ground → Connect to Jetson **Pin 34 (GND)**

**2. ESC - Electronic Speed Controller (3 wires)**

The ESC has a 3-wire servo connector:
- **White/Yellow** = Signal wire → Connect to Jetson **Pin 33**
- **Red** = Power output (BEC 5V) → Can power servo, do NOT connect to Jetson
- **Black/Brown** = Ground → Connect to Jetson **Pin 34 (GND)**

**3. Ground Connections**

⚠️ **CRITICAL:** All grounds must be connected together:
- Jetson GND pin (Pin 34)
- ESC ground wire (black)
- Servo ground wire (black/brown)
- RC car battery ground (via ESC)

This creates a common ground reference for all PWM signals.

**4. Power Setup**

- **ESC to Motor:** ESC main power wires connect to RC car motor (thick wires)
- **ESC to Battery:** ESC input connects to RC car battery pack
- **BEC (Battery Eliminator Circuit):** ESC provides 5V output via red wire to power servo
- **Jetson Power:** Jetson powered via 5V DC adapter (barrel jack or USB-C)
- **⚠️ Never connect servo/ESC 5V power to Jetson pins!**

#### Physical Connection Steps

1. **Power the Jetson:**
   - Connect 5V DC power adapter to Jetson's barrel jack or USB-C port
   - Ensure adequate power supply (typically 5V 4A for Jetson Nano)

2. **Connect USB gamepad** to Jetson USB port

3. **Locate Jetson GPIO Pins:**
   - Pin 32 (PWM0 - for steering)
   - Pin 33 (PWM2 - for throttle)
   - Pin 34 (GND - for common ground)

4. **Connect Steering Servo:**
   ```
   Servo 3-pin connector → Jetson
   [Orange] Signal -----> Pin 32
   [Red]    5V     -----> (From ESC BEC or external 5V - NOT Jetson!)
   [Brown]  GND    -----> Pin 34 (GND)
   ```

5. **Connect ESC:**
   ```
   ESC 3-pin connector → Jetson
   [White]  Signal -----> Pin 33
   [Red]    5V BEC -----> (Optional: to servo power)
   [Black]  GND    -----> Pin 34 (GND)
   ```

6. **Connect ESC to Motor:**
   - ESC thick wires → RC car brushed motor (2 or 3 wires)
   - If motor spins backward, swap any two motor wires

7. **Connect Power:**
   - ESC battery connector → RC car battery/power source
   - Jetson → 5V DC adapter (already done in step 1)

#### Wiring Diagram (Text)

```
    Steering Servo          Jetson GPIO Header
    [Signal] ─────────────> Pin 32 (PWM0)
    [5V Power] ←─────┐
    [Ground] ─────────┼───> Pin 34 (GND)
                      │
    ESC               │
    [Signal] ─────────┼───> Pin 33 (PWM2)
    [BEC 5V] ─────────┘
    [Ground] ─────────────> (Common GND)
    
    [Motor Wires] ──> Brushed Motor
    [Battery] ──────> RC Car Battery
    
    USB Gamepad ──────────> Jetson USB Port
```

## Module Structure

```
jetson_rc_control/
├── arduino/
│   └── rc_bridge.ino          # Legacy Arduino firmware (no longer needed)
├── jetson/
│   ├── teleop_rc.py           # Jetson teleoperation script (GPIO PWM)
│   ├── requirements.txt       # Python dependencies
│   ├── install_dependencies.bat   # Windows installer
│   ├── install_dependencies.sh    # Linux/Jetson installer
│   └── README.md              # Detailed Jetson setup
└── README.md                  # This file
```

## Setup Instructions

### 1. Jetson Setup

#### Quick Install (Recommended)

**On Linux/Jetson:**
```bash
cd jetson_rc_control/jetson
chmod +x install_dependencies.sh
./install_dependencies.sh
```

**On Windows (for testing without hardware):**
```powershell
cd jetson_rc_control\jetson
.\install_dependencies.bat
```

#### Manual Install

```bash
# Install Python packages
sudo pip3 install pygame Jetson.GPIO

# Verify installation
python3 -c "import pygame, Jetson.GPIO; print('Dependencies OK')"
```

#### Make Script Executable (Optional)

```bash
chmod +x jetson/teleop_rc.py
```

### 2. Hardware Connection

1. Power on the Jetson
2. Connect steering servo signal wire to Jetson **Pin 32**
3. Connect ESC signal wire to Jetson **Pin 33**
4. Connect common ground: Jetson **Pin 34** to servo/ESC grounds
5. Ensure servo has 5-6V power from ESC BEC or external supply
6. Power on the RC car (ESC should arm and recognize PWM signal)
7. Connect USB gamepad to Jetson

## Running the System

### Basic Usage

**Note:** Requires sudo for GPIO access

```bash
cd jetson
sudo python3 teleop_rc.py
```

### With Custom GPIO Pins

```bash
sudo python3 teleop_rc.py --steer-pin 32 --throttle-pin 33
```

### Command Line Options

```bash
sudo python3 teleop_rc.py --help
```

Options:
- `--steer-pin`: GPIO pin for steering (BOARD numbering, default: `32`)
- `--throttle-pin`: GPIO pin for throttle (BOARD numbering, default: `33`)
- `--deadzone`: Joystick deadzone (default: `0.1`)

## Controls

| Input | Action |
|-------|--------|
| Left Stick X-axis | Steering (left/right) |
| Left Stick Y-axis | Throttle (forward/reverse) |
| Ctrl+C | Emergency stop and exit |

## Testing Procedures

### 1. Neutral Behavior Test
- Start the system with joystick centered
- **Expected:** Wheels straight, motor off
- **Values:** Steering = 1500µs (7.5% duty), Throttle = 1500µs (7.5% duty)

### 2. Steering Test
- Move left stick left/right
- **Expected:** 
  - Full left → ~1000µs → wheels turn left
  - Full right → ~2000µs → wheels turn right

### 3. Throttle Test (Wheels Off Ground!)
- Push left stick forward/backward
- **Expected:**
  - Forward → motor spins forward
  - Backward → motor brakes/reverse (ESC dependent)

### 4. Emergency Stop Test
- While running, press Ctrl+C
- **Expected:** Neutral PWM set, motor stops immediately, GPIO cleaned up

## PWM Signal Details

**Frequency:** 50 Hz (20ms period)

**Pulse Width Range:** 1000–2000 microseconds

**Signal Level:** 3.3V (Jetson GPIO output)

| Value | Duty Cycle | Meaning |
|-------|------------|---------|
| 1000µs | 5.0% | Full left / Full reverse |
| 1500µs | 7.5% | Neutral / Center |
| 2000µs | 10.0% | Full right / Full forward |

## Safety Features

### GPIO Control
- **Emergency Stop:** Ctrl+C sets neutral PWM (1500µs) before cleanup
- **Input Clamping:** All PWM values clamped to safe range [1000, 2000]
- **GPIO Cleanup:** Proper GPIO cleanup on exit to prevent pin conflicts

### Python Script
- **Emergency Stop:** Ctrl+C sends neutral position before GPIO cleanup
- **Deadzone:** Small joystick movements (<0.1) ignored to prevent drift
- **Input Clamping:** Axis values clamped before conversion
- **Root Check:** Script verifies GPIO permissions at startup

## Troubleshooting

### No Joystick Found
```
ERROR: No joystick/gamepad found!
```
**Solution:** Connect USB gamepad and verify with:
```bash
ls /dev/input/js*
```

### GPIO Permission Error
```
ERROR: GPIO access denied!
```
**Solution:** Run with sudo:
```bash
sudo python3 teleop_rc.py
```

### Jetson.GPIO Not Installed
```
ERROR: Jetson.GPIO is not installed!
```
**Solution:** Install with sudo:
```bash
sudo pip3 install Jetson.GPIO
```

### Servo/ESC Not Responding
**Solutions:**
- Verify wiring: Pin 32 for steering, Pin 33 for throttle
- Check common ground connection between Jetson and RC electronics
- Ensure servo has external 5-6V power (not from Jetson!)
- Verify PWM signal with oscilloscope (3.3V, 50Hz, 1-2ms pulse)

### ESC Not Arming
**Solutions:**
- Verify neutral signal (1500µs / 7.5% duty) on startup
- Check ESC power and battery connections
- Consult ESC manual for arming procedure
- Some ESCs require full throttle → neutral sequence

### Steering/Throttle Reversed
**Solutions:**
- Swap servo connections physically, or
- Modify `axis_to_us()` function in Python to invert mapping

### Wrong Joystick Axes
**Solutions:**
- Run script with debug output (prints axis values)
- Adjust `STEER_AXIS` and `THROTTLE_AXIS` constants in [jetson/teleop_rc.py](jetson/teleop_rc.py)

## Configuration

### Arduino ([arduino/rc_bridge.ino](arduino/rc_bridge.ino))
- `STEERING_PIN`: Pin 9 (default)
- `THROTTLE_PIN`: Pin 10 (default)
- `SERIAL_TIMEOUT_MS`: 500ms (default)

### Python ([jetson/teleop_rc.py](jetson/teleop_rc.py))
- `SERIAL_PORT`: `/dev/ttyACM0` (default)
- `BAUD_RATE`: 115200 (default)
- `LOOP_HZ`: 50 Hz (default)
- `STEER_AXIS`: 0 (left stick X)
- `THROTTLE_AXIS`: 1 (left stick Y, inverted)
- `DEADZONE`: 0.1 (default)

## Integration with Larger Systems

This module provides a low-level control interface that can be integrated into higher-level autonomous systems:

### As a Standalone Component
- Direct manual control via USB gamepad
- Useful for testing, calibration, and manual operation
- Can be used to collect training data for autonomous systems

### Integration Points
- **Input:** Replace gamepad input with autonomous control commands
- **Serial Protocol:** Standard `S<steer> T<throttle>` format can be used by any controller
- **Python API:** Import `send_command()` function from `teleop_rc.py` for programmatic control
- **ROS Integration:** Can be wrapped as a ROS node for pub/sub control

### Example Integration
```python
import serial
from jetson_rc_control.jetson.teleop_rc import send_command

# Connect to Arduino
ser = serial.Serial('/dev/ttyACM0', 115200)

# Send control command from your autonomous system
steer_us = 1300  # Slight left turn
throttle_us = 1600  # Medium forward speed
send_command(ser, steer_us, throttle_us)
```

## License

This project is provided as-is for educational and hobby purposes.

## Safety Warning

⚠️ **IMPORTANT:**
- Always test with wheels off the ground first
- Ensure clear space around vehicle during operation
- Keep hands away from wheels when powered
- ESC/motor can generate significant torque
- Have emergency stop plan ready
