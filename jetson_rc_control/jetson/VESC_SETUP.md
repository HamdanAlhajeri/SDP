# VESC control setup

Manual teleoperation of the Slash 4x4 through the VESC, run from a terminal
with a monitor attached to the Jetson.

## Why not GPIO

`teleop_rc.py` generated PWM on the Jetson 40-pin header. On this build that
path does not work:

| Problem | Detail |
|---|---|
| Wrong pinout | The README pin table (32 = PWM0, 33 = PWM2) is the **Jetson Nano** pinout. This project runs an Orin NX, where those are not the PWM pins. |
| No device tree | `jetson-io` exits with `No DTB found for NVIDIA Jetson Orin NX Engineering Reference Developer Kit Super`, so the header cannot be re-muxed with the standard tool. |
| Frequency floor | The Tegra PWM clock divider rejects periods longer than ~5 ms. Measured: 5 ms (200 Hz) accepted, 10 ms and 20 ms (50 Hz) rejected. Standard servo timing is 50 Hz. |

The VESC already drives the steering servo and the motor, so the Jetson only
has to send it commands.

```
gamepad --USB--> Jetson --USB--> VESC --+--> steering servo
                                        +--> drive motor
```

## Files

| File | Purpose |
|---|---|
| `vesc_control.py` | VESC serial driver. Implements the packet protocol directly. Standard library only, so it runs on a Jetson with no internet. |
| `teleop_vesc.py` | Gamepad teleoperation through the VESC. Needs `pygame`. |
| `VESC_SETUP.md` | This file. |

Both scripts live in `jetson_rc_control/jetson/` and must stay in the same
directory — `teleop_vesc.py` imports `vesc_control`.

## One-time VESC configuration

Run VESC Tool on a laptop. The official Linux build is x86-64 only and will
not run on the Jetson. Settings are stored on the VESC itself, so this is
done once.

1. Connect the VESC to the laptop by USB, battery connected
2. **Connect** (it appears on a COM port / `/dev/ttyACM0`)
3. **App Settings -> General**
   - `APP to Use` = `UART`
   - `Enable Servo Output` = `True`
4. Write the app configuration
5. **Motor Settings -> FOC** — run the Motor Setup Wizard for the Velineon
   3500 (small inrunner, sensorless). Measured values for this motor:
   R = 6.40 mΩ, L = 2.48 µH
6. Set the 3S battery cutoffs: 10.2 V start, 9.0 V end

Steering that does not respond is almost always `Enable Servo Output` still
set to `False`, or written but not saved.

## Check the Jetson sees the VESC

```bash
ls -l /dev/ttyACM*
```

Expected:

```
crw-rw---- 1 root dialout 166, 0 /dev/ttyACM0
```

Nothing listed usually means a charge-only USB cable. Confirm the cable
carries data by plugging a phone into a computer with it.

To avoid needing `sudo` every time:

```bash
sudo usermod -aG dialout $USER
# log out and back in
```

## Stop the service first

`rc-teleop.service` starts on boot and holds `/dev/vesc` and `/dev/gamepad`.
A manual run will fail to open the port while it is running.

```bash
sudo systemctl stop rc-teleop
```

Start it again when you are done:

```bash
sudo systemctl start rc-teleop
```

## Test the steering

Wheels off the ground.

```bash
cd ~/jetson_rc_control/jetson
python3 vesc_control.py --test-servo
```

The front wheels should sweep left and right three times. No motor commands
are sent by this test.

If nothing moves:
- `Enable Servo Output` is not `True`, or was not written to the VESC
- the servo is not plugged into the VESC 3-pin servo port
- the battery is not connected, so the BEC is not producing 5 V

## Teleoperation

Steering and throttle, wheels off the ground:

```bash
python3 teleop_vesc.py
```

Steering only, motor cannot spin:

```bash
python3 teleop_vesc.py --disable-motor
```

| Control | Action |
|---|---|
| Left stick X | Steering |
| Left stick Y | Throttle (unless `--disable-motor` is used) |
| Ctrl+C | Stop, centre steering, exit |

Options:

| Flag | Default | Meaning |
|---|---|---|
| `--port` | `/dev/vesc` | VESC serial port, falls back to `/dev/ttyACM0` |
| `--deadzone` | `0.1` | Joystick deadzone |
| `--disable-motor` | off | Disable throttle commands for steering-only use |
| `--min-current` | `5.0` | Motor current at the joystick deadzone edge, amps |
| `--max-current` | `170.0` | Motor current at full joystick travel, amps |
| `--duty` | off | Use duty-cycle control instead of current control |

## Tuning

In `teleop_vesc.py`:

- `STEER_RANGE` (default `0.35`) sets how far the steering swings either side
  of centre. Widen it once the servo has been checked against the linkage end
  stops; the servo can otherwise stall against them and draw current
  continuously.
- `MIN_CURRENT` (default `5.0` A) sets the commanded current at the edge of the
  joystick deadzone. `MAX_CURRENT` (default `170.0` A) sets the current at full
  stick. Between those points, current scales smoothly with stick travel.

## Launch behaviour

Throttle uses **current control** (`COMM_SET_CURRENT`), not duty cycle.
Sensorless FOC startup is designed around current control: at low duty the
applied voltage is small and heavily rippled, which is the worst possible
input for the openloop routine and shows up as cogging and repeated ~70 A
current spikes at launch.

If launches from a dead stop are still rough, in VESC Tool under
**Motor Settings -> FOC -> Sensorless**:

| Setting | Change |
|---|---|
| Openloop Time Lock | 0 -> 0.05 s |
| Openloop ERPM | 1400 -> 2500 |
| Openloop Time Ramp | 0.1 -> 0.2 |
| Openloop Hysteresis | 0.10 -> 0.15 |

Openloop Time Lock is usually the single biggest improvement — it holds a DC
vector to pull the rotor to a known angle before rotating.

Do not sit there retrying a failed launch repeatedly. Each cycle is a shock
load into the pinion mesh and a thermal pulse into the FETs.

## Gamepad notes

The 8BitDo Ultimate 2.4G enumerates on Linux only with the rear mode switch
set to **D-input**. In X-input mode the kernel does not bind it and it never
appears in `/proc/bus/input/devices`, even though `lsusb` shows the receiver.

## Battery

This build runs a 3S pack (Venom 5500). Before connecting a 6S pack, check
`Motor Settings -> General -> Voltage` in VESC Tool: the cutoff values are
per-pack and a 3S configuration will fault on 6S.
