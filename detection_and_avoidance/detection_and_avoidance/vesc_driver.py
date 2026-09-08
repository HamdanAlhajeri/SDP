"""Small write-only VESC UART driver used by the avoidance node."""

import os
import struct
import termios


DEFAULT_PORT = '/dev/vesc'
FALLBACK_PORT = '/dev/ttyACM0'
SERVO_CENTER = 0.5

COMM_SET_DUTY = 5
COMM_SET_CURRENT = 6
COMM_SET_SERVO_POS = 12


def clamp(value, low, high):
    return max(low, min(high, value))


def crc16(data):
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = (((crc << 1) ^ 0x1021) if crc & 0x8000 else
                   (crc << 1)) & 0xffff
    return crc


def frame(payload):
    length = len(payload)
    if length < 256:
        header = bytes([2, length])
    else:
        header = bytes([3, length >> 8, length & 0xff])
    return header + payload + struct.pack('>H', crc16(payload)) + bytes([3])


class VESC:
    """VESC connection controlling motor current and steering servo."""

    def __init__(self, port=DEFAULT_PORT, baud=115200):
        if port == DEFAULT_PORT and not os.path.exists(port):
            port = FALLBACK_PORT
        if not os.path.exists(port):
            raise OSError('No VESC found at %s' % port)
        self.fd = os.open(port, os.O_RDWR | os.O_NOCTTY)
        attrs = termios.tcgetattr(self.fd)
        speed = getattr(termios, 'B%d' % baud, termios.B115200)
        attrs[0:4] = [0, 0, termios.CS8 | termios.CREAD | termios.CLOCAL, 0]
        attrs[4] = speed
        attrs[5] = speed
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    def _send(self, payload):
        os.write(self.fd, frame(payload))

    def set_servo_pos(self, position):
        position = clamp(position, 0.0, 1.0)
        self._send(struct.pack('>BH', COMM_SET_SERVO_POS,
                               int(position * 1000)))

    def set_current(self, amps):
        self._send(struct.pack('>Bi', COMM_SET_CURRENT, int(amps * 1000)))

    def set_duty(self, duty):
        duty = clamp(duty, -1.0, 1.0)
        self._send(struct.pack('>Bi', COMM_SET_DUTY, int(duty * 100000)))

    def stop(self):
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
