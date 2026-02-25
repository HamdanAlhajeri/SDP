# SDP - Robotics System Development Project

This repository contains modular robotics systems and control components for autonomous vehicle research and development.

## Overview

This project is organized into independent, reusable modules that can be integrated into larger autonomous systems. Each module is self-contained with its own documentation, dependencies, and testing procedures.

## Project Structure

```
SDP/
├── jetson_rc_control/         # Jetson-to-RC Car control module
│   ├── arduino/               # Arduino firmware
│   │   └── rc_bridge.ino      # PWM control sketch
│   ├── jetson/                # Jetson Python scripts
│   │   ├── teleop_rc.py       # Teleoperation script
│   │   ├── requirements.txt   # Python dependencies
│   │   ├── install_dependencies.sh   # Linux installer
│   │   ├── install_dependencies.bat  # Windows installer
│   │   └── README.md          # Jetson setup guide
│   └── README.md              # Module documentation
└── README.md                  # This file
```

## Modules

### Jetson RC Control
**Location:** [`jetson_rc_control/`](jetson_rc_control/)

A direct GPIO control system for RC vehicles using a Jetson board and USB gamepad. Provides low-latency PWM control without requiring an Arduino.

**Key Features:**
- USB gamepad input handling
- Direct GPIO PWM signal generation
- 50Hz PWM for servo/ESC control
- Safety features and emergency stop
- Configurable control mapping

**Arduino Not Required:** This system uses Jetson GPIO pins directly instead of serial communication to Arduino, reducing latency and simplifying hardware.

**Status:** ⚠️  To be tested 

See [jetson_rc_control/README.md](jetson_rc_control/README.md) for full documentation.

---

## Getting Started

Each module contains its own README with:
- Hardware requirements
- Software dependencies
- Setup instructions
- Usage examples
- Testing procedures

Navigate to the specific module directory to begin.

## Development Guidelines

### Module Structure

Each module should follow this structure:
```
module_name/
├── README.md              # Module documentation
├── src/                   # Source code
├── tests/                 # Test files
├── docs/                  # Additional documentation
└── examples/              # Usage examples
```

### Integration

Modules are designed to be:
- **Independent:** Can run standalone for testing
- **Composable:** Can be integrated into larger systems
- **Documented:** Clear interfaces and usage patterns
- **Tested:** Includes verification procedures

## Future Modules

Planned additions:
- Vision processing pipeline
- Sensor fusion module
- Path planning system
- Localization module
- Communication interface

## Contributing

When adding new modules:
1. Create a dedicated folder with descriptive name
2. Include comprehensive README.md
3. Document all dependencies
4. Provide testing procedures
5. Follow existing module patterns
