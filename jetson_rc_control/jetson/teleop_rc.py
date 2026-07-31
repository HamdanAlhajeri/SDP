#!/usr/bin/env python3
"""
Jetson RC control without Arduino.

Hardware assumption:
- VESC/ESC connector has 3 pins: signal, +5V/BEC, ground
- Steering controller/servo connector has 3 pins: signal, +5V, ground
- Jetson only drives the SIGNAL pins and shares GROUND
- Do not power the Jetson from the controller/servo red wire

Default wiring using Jetson BOARD numbering:
- Steering signal  -> Pin 32 / PWM0
- VESC/ESC signal  -> Pin 33 / PWM2
- Common ground    -> Pin 34 or any Jetson GND pin
- Red power wires  -> external 5-6V/BEC, not Jetson GPIO

Run:
    sudo python3 teleop_rc_no_arduino.py
"""

import argparse
import signal
import sys
import time
from dataclasses import dataclass

import pygame

try:
    import Jetson.GPIO as GPIO
except ImportError:
    print("ERROR: Jetson.GPIO is not installed.")
    print("Install it with: sudo pip3 install Jetson.GPIO pygame")
    sys.exit(1)


@dataclass(frozen=True)
class ThreePinPwmDevice:
    name: str
    signal_pin: int
    power_pin_label: str = "external 5-6V/BEC"
    ground_pin_label: str = "Jetson GND/common ground"
    min_us: int = 1000
    neutral_us: int = 1500
    max_us: int = 2000
    inverted: bool = False


PWM_FREQ_HZ = 50
PWM_PERIOD_US = 1_000_000 // PWM_FREQ_HZ
LOOP_HZ = 50
DEBUG_PRINT_HZ = 5

DEFAULT_STEERING = ThreePinPwmDevice(
    name="steering controller",
    signal_pin=32,
    inverted=False,
)
DEFAULT_VESC = ThreePinPwmDevice(
    name="VESC/ESC",
    signal_pin=33,
    inverted=False,
)

STEER_AXIS = 0       # Left stick X
THROTTLE_AXIS = 1    # Left stick Y
DEFAULT_DEADZONE = 0.10

running = True


def handle_shutdown(signum, frame):
    global running
    running = False


def clamp(value, low, high):
    return max(low, min(high, value))


def apply_deadzone(value: float, deadzone: float) -> float:
    if abs(value) < deadzone:
        return 0.0
    return value


def axis_to_us(axis_value: float, device: ThreePinPwmDevice) -> int:
    axis_value = clamp(axis_value, -1.0, 1.0)
    if device.inverted:
        axis_value = -axis_value

    half_range = (device.max_us - device.min_us) / 2.0
    pulse = device.neutral_us + axis_value * half_range
    return int(clamp(round(pulse), device.min_us, device.max_us))


def us_to_duty_cycle(pulse_us: int) -> float:
    return (pulse_us / PWM_PERIOD_US) * 100.0


def set_pwm(pwm, pulse_us: int):
    pwm.ChangeDutyCycle(us_to_duty_cycle(pulse_us))


def print_wiring(steering: ThreePinPwmDevice, vesc: ThreePinPwmDevice):
    print("\n3-pin wiring assumption:")
    print(f"  {steering.name}:")
    print(f"    signal -> Jetson BOARD pin {steering.signal_pin}")
    print(f"    power  -> {steering.power_pin_label}")
    print(f"    ground -> {steering.ground_pin_label}")
    print(f"  {vesc.name}:")
    print(f"    signal -> Jetson BOARD pin {vesc.signal_pin}")
    print(f"    power  -> VESC/ESC BEC or left unconnected to Jetson")
    print(f"    ground -> {vesc.ground_pin_label}")
    print("\nImportant: Jetson GPIO should connect to signal and ground only.")


def init_gamepad():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        raise RuntimeError("No USB gamepad found. Check /dev/input/js0 or reconnect the controller.")

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Gamepad: {joystick.get_name()}")
    print(f"Axes: {joystick.get_numaxes()} | Buttons: {joystick.get_numbuttons()}")
    return joystick


def init_pwm_outputs(steering: ThreePinPwmDevice, vesc: ThreePinPwmDevice):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(steering.signal_pin, GPIO.OUT)
    GPIO.setup(vesc.signal_pin, GPIO.OUT)

    pwm_steering = GPIO.PWM(steering.signal_pin, PWM_FREQ_HZ)
    pwm_vesc = GPIO.PWM(vesc.signal_pin, PWM_FREQ_HZ)

    pwm_steering.start(us_to_duty_cycle(steering.neutral_us))
    pwm_vesc.start(us_to_duty_cycle(vesc.neutral_us))

    # Give the VESC/ESC time to see a neutral command before throttle changes.
    time.sleep(1.0)
    return pwm_steering, pwm_vesc


def main():
    parser = argparse.ArgumentParser(description="Jetson RC teleop without Arduino")
    parser.add_argument("--steer-pin", type=int, default=DEFAULT_STEERING.signal_pin,
                        help="Jetson BOARD pin connected to steering signal")
    parser.add_argument("--vesc-pin", "--throttle-pin", dest="vesc_pin", type=int,
                        default=DEFAULT_VESC.signal_pin,
                        help="Jetson BOARD pin connected to VESC/ESC signal")
    parser.add_argument("--deadzone", type=float, default=DEFAULT_DEADZONE)
    parser.add_argument("--invert-steer", action="store_true")
    parser.add_argument("--invert-throttle", action="store_true")
    parser.add_argument("--steer-axis", type=int, default=STEER_AXIS)
    parser.add_argument("--throttle-axis", type=int, default=THROTTLE_AXIS)
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    steering = ThreePinPwmDevice(
        name="steering controller",
        signal_pin=args.steer_pin,
        inverted=args.invert_steer,
    )
    vesc = ThreePinPwmDevice(
        name="VESC/ESC",
        signal_pin=args.vesc_pin,
        inverted=args.invert_throttle,
    )

    print_wiring(steering, vesc)

    pwm_steering = None
    pwm_vesc = None

    try:
        joystick = init_gamepad()
        pwm_steering, pwm_vesc = init_pwm_outputs(steering, vesc)

        print("\nTeleoperation active")
        print("Left stick X: steering")
        print("Left stick Y: throttle")
        print("Ctrl+C: neutral stop and exit\n")

        loop_period = 1.0 / LOOP_HZ
        debug_period = 1.0 / DEBUG_PRINT_HZ
        last_debug = 0.0

        while running:
            start = time.time()
            pygame.event.pump()

            steer_raw = joystick.get_axis(args.steer_axis)
            throttle_raw = -joystick.get_axis(args.throttle_axis)

            steer_raw = apply_deadzone(steer_raw, args.deadzone)
            throttle_raw = apply_deadzone(throttle_raw, args.deadzone)

            steer_us = axis_to_us(steer_raw, steering)
            throttle_us = axis_to_us(throttle_raw, vesc)

            set_pwm(pwm_steering, steer_us)
            set_pwm(pwm_vesc, throttle_us)

            now = time.time()
            if now - last_debug >= debug_period:
                print(
                    f"steer={steer_us:4d}us ({steer_raw:+.2f}) | "
                    f"vesc={throttle_us:4d}us ({throttle_raw:+.2f})"
                )
                last_debug = now

            elapsed = time.time() - start
            if elapsed < loop_period:
                time.sleep(loop_period - elapsed)

    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}")
        print("Try running with sudo and confirm the selected pins support PWM.")
        sys.exit(1)
    finally:
        print("\nSetting both outputs to neutral...")
        if pwm_steering is not None:
            set_pwm(pwm_steering, steering.neutral_us)
        if pwm_vesc is not None:
            set_pwm(pwm_vesc, vesc.neutral_us)
        time.sleep(0.2)

        if pwm_steering is not None:
            pwm_steering.stop()
        if pwm_vesc is not None:
            pwm_vesc.stop()

        GPIO.cleanup()
        pygame.quit()
        print("Stopped safely.")


if __name__ == "__main__":
    main()