#!/usr/bin/env python3
"""
teleop_vesc.py -- gamepad teleoperation through the VESC.

The Jetson reads a gamepad and streams steering and drive commands to the
VESC over USB serial. The VESC generates the PWM for both the steering servo
and the motor, so no Jetson GPIO is involved.

Dependencies:
    pygame
    vesc_control.py (same directory, standard library only)

Usage:
    # steering and throttle, wheels off the ground first
    python3 teleop_vesc.py

    # steering only, motor cannot spin
    python3 teleop_vesc.py --disable-motor

    # override the current range
    python3 teleop_vesc.py --min-current 10 --max-current 120

    # reach full throttle in roughly 3.4 seconds after launch
    python3 teleop_vesc.py --launch-throttle 0.14 --ramp-rate 0.25

Controls:
    Left stick X  -> steering
    Left stick Y  -> throttle (unless --disable-motor is used)
    Ctrl+C        -> stop, centre steering, exit

Note on gamepads: the 8BitDo Ultimate 2.4G only enumerates on Linux with the
rear mode switch set to D-input. X-input is not claimed by xpad for this
variant.

Note on systemd: this script takes no terminal input, so it runs unchanged
under rc-teleop.service. Zero throttle is sent on startup and again on exit
via atexit.
"""

import sys
import time
import atexit
import argparse
import math

import pygame

from vesc_control import VESC, DEFAULT_PORT, SERVO_CENTER, clamp

# =============================================================================
# Configuration
# =============================================================================

STEER_AXIS = 0            # left stick X
THROTTLE_AXIS = 1         # left stick Y (inverted below)

DEADZONE = 0.1            # axis values below this read as zero
LOOP_HZ = 50              # VESC times out if it hears nothing, so resend
STEER_RANGE = 0.35        # 0.5 +/- 0.35 -> 0.15 .. 0.85
MIN_CURRENT = 5.0         # amps at the edge of the joystick deadzone
MAX_CURRENT = 170.0       # amps at full joystick travel
LAUNCH_THROTTLE = 0.1    # known-good initial sensorless launch command
RAMP_RATE = 0.25          # throttle units per second after launch
DEBUG_PRINT_HZ = 5


# =============================================================================
# Helpers
# =============================================================================

def apply_deadzone(value, deadzone):
    """Return 0 inside the deadzone, otherwise the raw value."""
    if abs(value) < deadzone:
        return 0.0
    return value


def axis_to_servo(x):
    """Map a joystick axis in [-1, 1] to a servo position in [0, 1]."""
    x = clamp(x, -1.0, 1.0)
    return SERVO_CENTER + (STEER_RANGE * x)


def throttle_to_current(throttle, deadzone, min_current, max_current):
    """Map throttle outside the deadzone to a signed current range."""
    if throttle == 0.0:
        return 0.0

    magnitude = (abs(throttle) - deadzone) / (1.0 - deadzone)
    magnitude = clamp(magnitude, 0.0, 1.0)
    current = min_current + (magnitude * (max_current - min_current))
    return current if throttle > 0.0 else -current


def ramp_throttle(commanded, target, elapsed, launch_throttle, ramp_rate):
    """Ramp acceleration while allowing an immediate reduction or stop.

    A new command starts at ``launch_throttle`` (or the target when lower),
    because this motor is already known to launch cleanly around 0.14. Power
    then rises by at most ``ramp_rate`` throttle units per second.
    """
    if target == 0.0:
        return 0.0

    # Never ramp through zero into reverse. Stop for one loop first.
    if commanded != 0.0 and math.copysign(1.0, commanded) != math.copysign(
            1.0, target):
        return 0.0

    if commanded == 0.0:
        return math.copysign(min(abs(target), launch_throttle), target)

    # Reducing the stick must reduce power immediately.
    if abs(target) <= abs(commanded):
        return target

    next_magnitude = min(abs(target),
                         abs(commanded) + ramp_rate * elapsed)
    return math.copysign(next_magnitude, target)


def find_joystick(attempts=10):
    """
    Scan for a gamepad and return an initialised joystick, or None.

    Do not call pygame.joystick.quit() after opening a joystick. It tears
    down the subsystem and leaves this handle dangling, which segfaults on
    the next call.
    """
    pygame.init()
    pygame.joystick.init()

    for i in range(attempts):
        pygame.event.pump()
        if pygame.joystick.get_count() > 0:
            js = pygame.joystick.Joystick(0)
            js.init()
            print("Gamepad: %s (%d axes)" % (js.get_name(), js.get_numaxes()))
            return js
        print("No gamepad yet, retrying (%d/%d)" % (i + 1, attempts))
        time.sleep(1.0)

    return None


# =============================================================================
# Main loop
# =============================================================================

def main():
    p = argparse.ArgumentParser(description="Gamepad teleop via VESC")
    p.add_argument("--port", default=DEFAULT_PORT,
                   help="VESC serial port (default: %s)" % DEFAULT_PORT)
    p.add_argument("--deadzone", type=float, default=DEADZONE)
    p.add_argument("--disable-motor", dest="enable_motor",
                   action="store_false", default=True,
                   help="disable throttle commands (steering only)")
    p.add_argument("--min-current", type=float, default=MIN_CURRENT,
                   help="motor current at the deadzone edge in amps "
                        "(default: %.1f)" % MIN_CURRENT)
    p.add_argument("--max-current", type=float, default=MAX_CURRENT,
                   help="motor current at full throttle in amps (default: %.1f)"
                        % MAX_CURRENT)
    p.add_argument("--launch-throttle", type=float, default=LAUNCH_THROTTLE,
                   help="initial throttle used when launching (default: %.2f)"
                        % LAUNCH_THROTTLE)
    p.add_argument("--ramp-rate", type=float, default=RAMP_RATE,
                   help="maximum throttle increase per second (default: %.2f)"
                        % RAMP_RATE)
    p.add_argument("--duty", action="store_true",
                   help="use duty-cycle control instead of current control")
    args = p.parse_args()

    if not math.isfinite(args.deadzone) or not 0.0 <= args.deadzone < 1.0:
        p.error("--deadzone must be at least 0 and less than 1")
    if not math.isfinite(args.min_current) or args.min_current < 0.0:
        p.error("--min-current must be a non-negative finite value")
    if (not math.isfinite(args.max_current)
            or args.max_current < args.min_current):
        p.error("--max-current must be finite and at least --min-current")
    if (not math.isfinite(args.launch_throttle)
            or not args.deadzone <= args.launch_throttle <= 1.0):
        p.error("--launch-throttle must be between --deadzone and 1")
    if not math.isfinite(args.ramp_rate) or args.ramp_rate <= 0.0:
        p.error("--ramp-rate must be a positive finite value")

    vesc = VESC(args.port)

    # Always leave the car stopped, however this process exits.
    atexit.register(vesc.close)
    vesc.stop()

    js = find_joystick()
    if js is None:
        print("No gamepad found. Exiting.")
        return 1

    if not args.enable_motor:
        print("Motor DISABLED (steering only).")
    elif args.duty:
        print("Motor ENABLED in duty-cycle mode. Wheels off the ground.")
    else:
        print("Motor ENABLED, current range %.1f-%.1f A. "
              "Wheels off the ground."
              % (args.min_current, args.max_current))

    period = 1.0 / LOOP_HZ
    print_every = max(1, int(LOOP_HZ / DEBUG_PRINT_HZ))
    tick = 0
    commanded_throttle = 0.0
    previous_time = time.monotonic()

    try:
        while True:
            pygame.event.pump()

            steer = apply_deadzone(js.get_axis(STEER_AXIS), args.deadzone)
            servo = axis_to_servo(steer)
            vesc.set_servo_pos(servo)

            target_throttle = 0.0
            if args.enable_motor:
                # Y axis is inverted: pushing forward reads negative.
                target_throttle = -apply_deadzone(
                    js.get_axis(THROTTLE_AXIS), args.deadzone)
                target_throttle = clamp(target_throttle, -1.0, 1.0)

                now = time.monotonic()
                elapsed = min(now - previous_time, 0.1)
                previous_time = now
                commanded_throttle = ramp_throttle(
                    commanded_throttle, target_throttle, elapsed,
                    args.launch_throttle, args.ramp_rate)

                if args.duty:
                    vesc.set_duty(commanded_throttle * 0.15)
                else:
                    # Current control. Sensorless startup is designed around
                    # this; duty at low speed gives the openloop routine a
                    # rippled, undefined torque and causes launch cogging.
                    current = throttle_to_current(
                        commanded_throttle, args.deadzone,
                        args.min_current, args.max_current)
                    vesc.set_current(current)
            else:
                vesc.set_current(0.0)

            tick += 1
            if tick % print_every == 0:
                print("steer %+.2f -> servo %.2f | throttle target %+.2f "
                      "commanded %+.2f"
                      % (steer, servo, target_throttle,
                         commanded_throttle))

            time.sleep(period)

    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        vesc.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
