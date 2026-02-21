#!/usr/bin/env python3
"""
RC Car Teleoperation Script for Jetson

Reads USB gamepad input and sends PWM commands to Arduino
via serial to control steering and throttle on Traxxas RC car.

Dependencies:
    - pygame
    - pyserial

Install with:
    pip3 install pygame pyserial
    
Usage:
    python3 teleop_rc.py [--port /dev/ttyACM0]
"""

import sys
import time
import argparse
import pygame

# Import pyserial with error handling for common installation issues
try:
    import serial
    # Verify it's the correct pyserial module
    if not hasattr(serial, 'Serial'):
        raise ImportError("Wrong serial module - pyserial not installed correctly")
except ImportError as e:
    print("=" * 70)
    print("ERROR: pyserial is not properly installed!")
    print("=" * 70)
    print("\nThe 'serial' module was found, but it's not the pyserial library.")
    print("\nTo fix this, run these commands:")
    print("  1. pip uninstall serial")
    print("  2. pip install pyserial")
    print("\nOr in one command:")
    print("  pip uninstall serial -y && pip install pyserial")
    print("\n" + "=" * 70)
    sys.exit(1)

# =============================================================================
# Configuration Constants
# =============================================================================

SERIAL_PORT = "/dev/ttyACM0"  # Default Arduino serial port
BAUD_RATE = 115200            # Serial baud rate
LOOP_HZ = 50                  # Control loop frequency (Hz)

# Joystick axis indices (adjust for your gamepad if needed)
STEER_AXIS = 0                # Left stick X-axis
THROTTLE_AXIS = 1             # Left stick Y-axis (will be inverted)

# Deadzone threshold (values with abs < DEADZONE treated as 0)
DEADZONE = 0.1

# PWM pulse width range (microseconds)
MIN_US = 1000
MAX_US = 2000
NEUTRAL_US = 1500

# Debug print rate (Hz)
DEBUG_PRINT_HZ = 5

# =============================================================================
# Helper Functions
# =============================================================================

def axis_to_us(x: float) -> int:
    """
    Convert joystick axis value to PWM microseconds.
    
    Args:
        x: Axis value in range [-1.0, 1.0]
        
    Returns:
        PWM pulse width in microseconds [1000, 2000]
    """
    # Clamp input to [-1, 1]
    x = max(-1.0, min(1.0, x))
    # Map to [1000, 2000]
    return int(NEUTRAL_US + 500 * x)


def apply_deadzone(value: float, deadzone: float) -> float:
    """
    Apply deadzone to joystick axis value.
    
    Args:
        value: Raw axis value
        deadzone: Deadzone threshold
        
    Returns:
        Adjusted value (0 if within deadzone)
    """
    if abs(value) < deadzone:
        return 0.0
    return value


def send_command(ser: serial.Serial, steer_us: int, throttle_us: int):
    """
    Send control command to Arduino via serial.
    
    Args:
        ser: Serial connection object
        steer_us: Steering PWM in microseconds
        throttle_us: Throttle PWM in microseconds
    """
    command = f"S{steer_us} T{throttle_us}\n"
    ser.write(command.encode('utf-8'))


# =============================================================================
# Main Function
# =============================================================================

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='RC Car Teleoperation')
    parser.add_argument('--port', type=str, default=SERIAL_PORT,
                        help=f'Serial port (default: {SERIAL_PORT})')
    parser.add_argument('--baud', type=int, default=BAUD_RATE,
                        help=f'Baud rate (default: {BAUD_RATE})')
    parser.add_argument('--deadzone', type=float, default=DEADZONE,
                        help=f'Joystick deadzone (default: {DEADZONE})')
    args = parser.parse_args()
    
    # Initialize pygame
    print("Initializing pygame...")
    pygame.init()
    pygame.joystick.init()
    
    # Check for joystick
    if pygame.joystick.get_count() == 0:
        print("ERROR: No joystick/gamepad found!")
        print("Please connect a USB gamepad and try again.")
        sys.exit(1)
    
    # Initialize first joystick
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Found joystick: {joystick.get_name()}")
    print(f"  Axes: {joystick.get_numaxes()}")
    print(f"  Buttons: {joystick.get_numbuttons()}")
    
    # Initialize serial connection
    print(f"Connecting to Arduino on {args.port} at {args.baud} baud...")
    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.1)
        time.sleep(2)  # Wait for Arduino to reset after serial connection
        print("Serial connection established!")
    except serial.SerialException as e:
        print(f"ERROR: Failed to open serial port {args.port}")
        print(f"  {e}")
        print("\nTroubleshooting:")
        print("  - Check that Arduino is connected via USB")
        print("  - Verify the correct port (try: ls /dev/ttyACM* or ls /dev/ttyUSB*)")
        print("  - Ensure you have permissions (add user to 'dialout' group)")
        pygame.quit()
        sys.exit(1)
    
    # Control loop setup
    loop_period = 1.0 / LOOP_HZ
    debug_print_period = 1.0 / DEBUG_PRINT_HZ
    last_print_time = 0
    
    print("\n" + "="*60)
    print("RC CAR TELEOPERATION ACTIVE")
    print("="*60)
    print("Controls:")
    print("  Left Stick X-axis: Steering")
    print("  Left Stick Y-axis: Throttle (forward/reverse)")
    print("  Press Ctrl+C to exit safely")
    print("="*60 + "\n")
    
    try:
        while True:
            loop_start_time = time.time()
            
            # Pump pygame event queue
            pygame.event.pump()
            
            # Read joystick axes
            steer_raw = joystick.get_axis(STEER_AXIS)
            throttle_raw = -joystick.get_axis(THROTTLE_AXIS)  # Invert Y-axis
            
            # Apply deadzone
            steer_raw = apply_deadzone(steer_raw, args.deadzone)
            throttle_raw = apply_deadzone(throttle_raw, args.deadzone)
            
            # Convert to microseconds
            steer_us = axis_to_us(steer_raw)
            throttle_us = axis_to_us(throttle_raw)
            
            # Send command to Arduino
            send_command(ser, steer_us, throttle_us)
            
            # Debug output at reduced rate
            current_time = time.time()
            if current_time - last_print_time >= debug_print_period:
                print(f"Steer: {steer_us:4d}µs ({steer_raw:+.2f})  |  "
                      f"Throttle: {throttle_us:4d}µs ({throttle_raw:+.2f})")
                last_print_time = current_time
            
            # Maintain loop rate
            elapsed = time.time() - loop_start_time
            if elapsed < loop_period:
                time.sleep(loop_period - elapsed)
    
    except KeyboardInterrupt:
        print("\n\nShutdown signal received...")
    
    finally:
        # Emergency stop: send neutral command
        print("Sending neutral command (emergency stop)...")
        send_command(ser, NEUTRAL_US, NEUTRAL_US)
        time.sleep(0.1)  # Give time for command to be sent
        
        # Cleanup
        print("Closing serial connection...")
        ser.close()
        
        print("Shutting down pygame...")
        pygame.quit()
        
        print("Teleoperation stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
