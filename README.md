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

A complete teleoperation system for controlling RC vehicles using a Jetson board, Arduino, and USB gamepad. Provides low-latency PWM control over serial communication for steering and throttle.

**Key Features:**
- USB gamepad input handling
- Serial communication protocol
- PWM signal generation for servo/ESC
- Safety timeout and emergency stop
- Configurable control mapping

**Status:** ✅ Operational

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

## License

This project is provided for educational and research purposes.

## Contributing

When adding new modules:
1. Create a dedicated folder with descriptive name
2. Include comprehensive README.md
3. Document all dependencies
4. Provide testing procedures
5. Follow existing module patterns

## Safety Notice

⚠️ **Important:** These systems control physical hardware. Always:
- Test in safe, controlled environments
- Implement emergency stop mechanisms
- Follow module-specific safety guidelines
- Ensure proper grounding and power management
