# Jetson-to-RC Car Control System

Minimal working system for controlling a Traxxas RC car using a Jetson board and Arduino via USB gamepad teleoperation.

> **Module:** This is a standalone control module within the larger SDP robotics project. It can be used independently or integrated into autonomous vehicle systems.

## System Overview

**Data Flow:**
```
USB Gamepad → Jetson (Python) → Arduino (Serial) → PWM Signals → RC Car (Servo + ESC)
```

## Hardware Requirements

- **Jetson Board** (Nano/Xavier/Orin with Linux + Python 3)
- **Arduino Uno/Nano** (connected to Jetson via USB)
- **USB Gamepad** (Xbox/PlayStation/Generic)
- **Traxxas RC Car** with:
  - 1× Steering servo
  - 1× ESC (Electronic Speed Controller)

### Wiring Connections

#### Overview Table

| Component | Connection | Arduino Pin |
|-----------|------------|-------------|
| Steering Servo Signal Wire | → | Digital Pin D9 |
| ESC (Motor Controller) Signal Wire | → | Digital Pin D10 |
| Common Ground | → | GND Pin |
| Servo Power (5V) | ← | From ESC BEC |

#### Detailed Wiring Guide

**1. Steering Servo (3 wires)**

Standard servo wire colors:
- **Orange/Yellow/White** = Signal wire → Connect to Arduino **Pin D9**
- **Red** = Power (5V) → Connect to ESC BEC 5V output OR Arduino 5V pin
- **Brown/Black** = Ground → Connect to Arduino **GND** pin

**2. ESC - Electronic Speed Controller (3 wires to Arduino)**

The ESC has a 3-wire servo connector:
- **White/Yellow** = Signal wire → Connect to Arduino **Pin D10**
- **Red** = Power output (BEC 5V) → Can power servo, do NOT connect to Arduino 5V
- **Black/Brown** = Ground → Connect to Arduino **GND** pin

**3. Ground Connections**

⚠️ **CRITICAL:** All grounds must be connected together:
- Arduino GND pin
- ESC ground wire (black)
- Servo ground wire (black/brown)
- RC car battery ground (via ESC)

This creates a common ground reference for all PWM signals.

**4. Power Setup**

- **ESC to Motor:** ESC main power wires connect to RC car motor (thick wires)
- **ESC to Battery:** ESC input connects to RC car battery pack
- **BEC (Battery Eliminator Circuit):** ESC provides 5V output via red wire to power servo
- **Arduino Power:** Arduino powered via USB from Jetson (no additional power needed)

#### Physical Connection Steps

1. **Locate Arduino Pins:**
   - Pin D9 (Digital pin 9)
   - Pin D10 (Digital pin 10)  
   - GND pin (any ground pin)

2. **Connect Steering Servo:**
   ```
   Servo 3-pin connector → Arduino
   [Orange] Signal -----> D9
   [Red]    5V     -----> (From ESC BEC or Arduino 5V)
   [Brown]  GND    -----> GND
   ```

3. **Connect ESC:**
   ```
   ESC 3-pin connector → Arduino
   [White]  Signal -----> D10
   [Red]    5V BEC -----> (Optional: to servo power)
   [Black]  GND    -----> GND
   ```

4. **Connect ESC to Motor:**
   - ESC thick wires → RC car brushed motor (2 or 3 wires)
   - If motor spins backward, swap any two motor wires

5. **Connect Power:**
   - ESC battery connector → RC car battery/power source
   - Arduino → USB cable to Jetson

#### Wiring Diagram (Text)

```
                    Arduino Uno/Nano
                   ┌─────────────────┐
    Steering       │                 │
    Servo ────────>│ D9 (PWM)        │
   [Signal]        │                 │
                   │                 │
    ESC ──────────>│ D10 (PWM)       │
   [Signal]        │                 │
                   │                 │
    Common ───────>│ GND             │<───── ESC [Black]
    Ground         │                 │       Servo [Brown]
                   │                 │
    USB to   <────>│ USB Port        │
    Jetson         └─────────────────┘
                           │
                           │ USB Cable
                           ↓
                    Jetson Board
                           ↑
                    USB Gamepad
```

## Module Structure

```
jetson_rc_control/
├── arduino/
│   └── rc_bridge.ino          # Arduino firmware
├── jetson/
│   ├── teleop_rc.py           # Jetson teleoperation script
│   └── README.md              # Detailed Jetson setup
└── README.md                  # This file
```

## Setup Instructions

### 1. Arduino Setup

1. Open [arduino/rc_bridge.ino](arduino/rc_bridge.ino) in Arduino IDE
2. Select your Arduino board (Tools → Board)
3. Select the correct COM port (Tools → Port)
4. Upload the sketch to Arduino
5. Verify in Serial Monitor (115200 baud):
   - Should see "RC Bridge Initialized"

### 2. Jetson Setup

#### Install Dependencies

```bash
# Install Python packages
pip3 install pygame pyserial

# Optional: Add user to dialout group for serial permissions
sudo usermod -aG dialout $USER
# Log out and back in for changes to take effect
```

#### Find Arduino Serial Port

```bash
# List USB serial devices
ls /dev/ttyACM*  # Usually /dev/ttyACM0
ls /dev/ttyUSB*  # Or /dev/ttyUSB0
```

#### Make Script Executable (Optional)

```bash
chmod +x jetson/teleop_rc.py
```

### 3. Hardware Connection

1. Connect Arduino to Jetson via USB
2. Connect steering servo signal wire to Arduino pin D9
3. Connect ESC signal wire to Arduino pin D10
4. Ensure common ground between ESC, servo, and Arduino
5. Power on the RC car (ESC should arm after 2 seconds)
6. Connect USB gamepad to Jetson

## Running the System

### Basic Usage

```bash
cd jetson
python3 teleop_rc.py
```

### With Custom Serial Port

```bash
python3 teleop_rc.py --port /dev/ttyUSB0
```

### Command Line Options

```bash
python3 teleop_rc.py --help
```

Options:
- `--port`: Serial port (default: `/dev/ttyACM0`)
- `--baud`: Baud rate (default: `115200`)
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
- **Values:** Steering = 1500µs, Throttle = 1500µs

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
- **Expected:** Neutral command sent, motor stops immediately

## Serial Protocol

**Format:** `S<steer_us> T<throttle_us>\n`

**Example:** `S1500 T1600\n`

**Range:** 1000–2000 microseconds

| Value | Meaning |
|-------|---------|
| 1000µs | Full left / Full reverse |
| 1500µs | Neutral / Center |
| 2000µs | Full right / Full forward |

## Safety Features

### Arduino
- **Timeout Protection:** If no serial data for >500ms, throttle gradually returns to neutral (1500µs)
- **Input Clamping:** All PWM values clamped to safe range [1000, 2000]
- **Malformed Command Handling:** Invalid commands ignored; last known values maintained

### Python Script
- **Emergency Stop:** Ctrl+C sends neutral command before exit
- **Deadzone:** Small joystick movements (<0.1) ignored to prevent drift
- **Input Clamping:** Axis values clamped before conversion

## Troubleshooting

### No Joystick Found
```
ERROR: No joystick/gamepad found!
```
**Solution:** Connect USB gamepad and verify with:
```bash
ls /dev/input/js*
```

### Serial Port Error
```
ERROR: Failed to open serial port
```
**Solutions:**
- Check Arduino is connected: `ls /dev/ttyACM*`
- Verify user permissions: `sudo usermod -aG dialout $USER` (then log out/in)
- Try different port with `--port` option

### ESC Not Arming
**Solutions:**
- Verify neutral signal (1500µs) on startup
- Check ESC power and connections
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
