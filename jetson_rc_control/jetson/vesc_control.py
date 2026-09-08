#!/usr/bin/env python3
"""
vesc_control.py -- minimal VESC serial driver.

Standard library only. Implements the VESC binary packet protocol directly
over the USB CDC-ACM port, so nothing needs to be installed on the Jetson.

The VESC drives both the steering servo and the brushless motor, so the
Jetson only has to send it commands.

One-time VESC Tool setup:
    App Settings -> General -> APP to Use          = UART
    App Settings -> General -> Enable Servo Output = True
    then write the app configuration.

Self test (wheels off the ground):
    python3 vesc_control.py --test-servo
"""

import os
import sys
import time
import struct
import termios
import argparse

DEFAULT_PORT = "/dev/vesc"          # udev symlink; /dev/ttyACM0 also works
FALLBACK_PORT = "/dev/ttyACM0"

SERVO_CENTER = 0.5

# VESC command IDs
COMM_SET_DUTY = 5
COMM_SET_CURRENT = 6
COMM_SET_CURRENT_BRAKE = 7
COMM_SET_RPM = 8
COMM_SET_SERVO_POS = 12


def clamp(value, low, high):
    """Constrain value to [low, high]."""
    return max(low, min(high, value))


def crc16(data: bytes) -> int:
    """CRC-16/XMODEM, as used by the VESC packet format."""
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def frame(payload: bytes) -> bytes:
    """Wrap a payload in a VESC packet: start, length, payload, CRC, end."""
    length = len(payload)
    if length < 256:
        header = bytes([2, length])
    else:
        header = bytes([3, (length >> 8) & 0xFF, length & 0xFF])
    return header + payload + struct.pack(">H", crc16(payload)) + bytes([3])


class VESC:
    """Write-only VESC connection. Opens the port with raw termios settings."""

    def __init__(self, port=DEFAULT_PORT, baud=115200):
        if not os.path.exists(port) and port == DEFAULT_PORT:
            port = FALLBACK_PORT

        if not os.path.exists(port):
            raise IOError(
                "No VESC found at %s.\n"
                "  - check the USB cable actually carries data "
                "(charge-only cables will not enumerate)\n"
                "  - check `ls -l /dev/ttyACM*`\n"
                "  - if rc-teleop.service is running it already holds the "
                "port: sudo systemctl stop rc-teleop" % port
            )

        self.port = port
        self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
        self._configure(baud)

    def _configure(self, baud):
        attrs = termios.tcgetattr(self.fd)
        speed = getattr(termios, "B%d" % baud, termios.B115200)

        # raw mode
        attrs[0] = 0                                   # iflag
        attrs[1] = 0                                   # oflag
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL  # cflag
        attrs[3] = 0                                   # lflag
        attrs[4] = speed                               # ispeed
        attrs[5] = speed                               # ospeed
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0

        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def _send(self, payload: bytes):
        os.write(self.fd, frame(payload))

    # -- commands ---------------------------------------------------------

    def set_servo_pos(self, pos: float):
        """Steering. pos in [0.0, 1.0], 0.5 is centre."""
        pos = clamp(pos, 0.0, 1.0)
        self._send(struct.pack(">BH", COMM_SET_SERVO_POS, int(pos * 1000)))

    def set_current(self, amps: float):
        """Torque control. Preferred for launching from standstill."""
        self._send(struct.pack(">Bi", COMM_SET_CURRENT, int(amps * 1000)))

    def set_duty(self, duty: float):
        """Duty-cycle control. duty in [-1.0, 1.0]."""
        duty = clamp(duty, -1.0, 1.0)
        self._send(struct.pack(">Bi", COMM_SET_DUTY, int(duty * 100000)))

    def set_rpm(self, erpm: int):
        self._send(struct.pack(">Bi", COMM_SET_RPM, int(erpm)))

    def brake(self, amps: float):
        self._send(struct.pack(">Bi", COMM_SET_CURRENT_BRAKE,
                               int(abs(amps) * 1000)))

    def stop(self):
        """Zero the motor and centre the steering. Safe to call repeatedly."""
        try:
            self.set_current(0.0)
            self.set_duty(0.0)
            self.set_servo_pos(SERVO_CENTER)
        except OSError:
            pass

    def close(self):
        self.stop()
        try:
            os.close(self.fd)
        except OSError:
            pass


def test_servo(port):
    """Sweep the steering three times. Sends no motor commands."""
    v = VESC(port)
    print("Sweeping steering. Wheels off the ground. Ctrl+C to stop.")
    try:
        for i in range(3):
            for pos in (0.3, 0.5, 0.7, 0.5):
                print("  servo -> %.2f" % pos)
                v.set_servo_pos(pos)
                time.sleep(0.5)
        print("Done. If nothing moved, check Enable Servo Output = True.")
    finally:
        v.close()


def main():
    p = argparse.ArgumentParser(description="VESC driver self test")
    p.add_argument("--port", default=DEFAULT_PORT)
    p.add_argument("--test-servo", action="store_true",
                   help="sweep the steering servo, no motor commands")
    args = p.parse_args()

    # sanity check the CRC against the standard XMODEM check value
    assert crc16(b"123456789") == 0x31C3, "CRC implementation is wrong"

    if args.test_servo:
        test_servo(args.port)
    else:
        print("Nothing to do. Try --test-servo")


if __name__ == "__main__":
    sys.exit(main())
