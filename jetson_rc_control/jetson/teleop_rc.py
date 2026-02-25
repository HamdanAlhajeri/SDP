#!/usr/bin/env python3
"""
RC Car Teleoperation Script for Jetson

Reads USB gamepad input and generates PWM signals directly from
Jetson GPIO pins to control steering and throttle on Traxxas RC car.

Dependencies:
    - pygame
    - Jetson.GPIO

Install with:
    pip3 install pygame Jetson.GPIO
    
Usage:
    sudo python3 teleop_rc.py [--steer-pin 32] [--throttle-pin 33]
    
Note: Requires sudo for GPIO access
"""

import sys
import time
import argparse
import pygame

# Import Jetson.GPIO with error handling
try:
    import Jetson.GPIO as GPIO
except ImportError:
    print("=" * 70)
    print("ERROR: Jetson.GPIO is not installed!")
    print("=" * 70)
    print("\nThe Jetson.GPIO library is required for PWM control.")
    print("\nTo fix this, run:")
    print("  sudo pip3 install Jetson.GPIO")
    print("\nOr using the requirements file:")
    print("  sudo pip3 install -r requirements.txt")
    print("\n" + "=" * 70)
    sys.exit(1)
except RuntimeError as e:
    print("=" * 70)
    print("ERROR: GPIO access denied!")
    print("=" * 70)
    print("\nThis script requires root privileges to access GPIO pins.")
    print("\nPlease run with sudo:")
    print("  sudo python3 teleop_rc.py")
    print("\n" + "=" * 70)
    sys.exit(1)

# =============================================================================
# Configuration Constants
# =============================================================================

# GPIO pin assignments (BOARD numbering)
STEER_PIN = 32                # Steering servo signal pin (PWM0)
THROTTLE_PIN = 33             # ESC throttle signal pin (PWM2)

# PWM configuration
PWM_FREQ_HZ = 50              # Standard RC servo/ESC frequency
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
PWM_PERIOD_US = 20000         # Period at 50Hz = 20ms = 20000µs

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


def us_to_duty_cycle(pulse_us: int) -> float:
    """
    Convert pulse width in microseconds to PWM duty cycle percentage.
    
    Args:
        pulse_us: Pulse width in microseconds
        
    Returns:
        Duty cycle as percentage (0-100)
    """
    return (pulse_us / PWM_PERIOD_US) * 100.0


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


def set_pwm(pwm_steer, pwm_throttle, steer_us: int, throttle_us: int):
    """
    Set PWM duty cycles for steering and throttle.
    
    Args:
        pwm_steer: GPIO.PWM object for steering
        pwm_throttle: GPIO.PWM object for throttle
        steer_us: Steering PWM in microseconds
        throttle_us: Throttle PWM in microseconds
    """
    steer_duty = us_to_duty_cycle(steer_us)
    throttle_duty = us_to_duty_cycle(throttle_us)
    
    pwm_steer.ChangeDutyCycle(steer_duty)
    pwm_throttle.ChangeDutyCycle(throttle_duty)


# =============================================================================
# Main Function
# =============================================================================

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='RC Car Teleoperation')
    parser.add_argument('--steer-pin', type=int, default=STEER_PIN,
                        help=f'GPIO pin for steering (BOARD numbering, default: {STEER_PIN})')
    parser.add_argument('--throttle-pin', type=int, default=THROTTLE_PIN,
                        help=f'GPIO pin for throttle (BOARD numbering, default: {THROTTLE_PIN})')
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
    
    # Initialize GPIO
    print(f"\nInitializing GPIO pins...")
    print(f"  Steering: Pin {args.steer_pin}")
    print(f"  Throttle: Pin {args.throttle_pin}")
    
    try:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(args.steer_pin, GPIO.OUT)
        GPIO.setup(args.throttle_pin, GPIO.OUT)
        
        # Create PWM objects at 50Hz
        pwm_steer = GPIO.PWM(args.steer_pin, PWM_FREQ_HZ)
        pwm_throttle = GPIO.PWM(args.throttle_pin, PWM_FREQ_HZ)
        
        # Start PWM at neutral position
        neutral_duty = us_to_duty_cycle(NEUTRAL_US)
        pwm_steer.start(neutral_duty)
        pwm_throttle.start(neutral_duty)
        
        print("GPIO PWM initialized!")
        time.sleep(0.5)  # Allow ESC to recognize signal
        
    except Exception as e:
        print(f"ERROR: Failed to initialize GPIO")
        print(f"  {e}")
        print("\nTroubleshooting:")
        print("  - Run with sudo: sudo python3 teleop_rc.py")
        print("  - Check that pins are not in use by another process")
        print("  - Verify Jetson.GPIO is properly installed")
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
            
            # Set PWM outputs
            set_pwm(pwm_steer, pwm_throttle, steer_us, throttle_us)
            
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
        # Emergency stop: set neutral position
        print("Setting neutral position (emergency stop)...")
        set_pwm(pwm_steer, pwm_throttle, NEUTRAL_US, NEUTRAL_US)
        time.sleep(0.1)  # Give time for PWM to settle
        
        # Cleanup GPIO
        print("Stopping PWM signals...")
        pwm_steer.stop()
        pwm_throttle.stop()
        
        print("Cleaning up GPIO...")
        GPIO.cleanup()
        
        print("Shutting down pygame...")
        pygame.quit()
        
        print("Teleoperation stopped. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
