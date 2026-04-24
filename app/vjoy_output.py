"""
vjoy_output.py

Wraps the pyvjoy library to output processed axis values to a
vJoy virtual joystick device that Windows (and games) can see.

Requirements:
  1. Install vJoy driver: https://sourceforge.net/projects/vjoystick/
     - Enable Device 1 with axes X, Y, Z and at least 1 button
  2. pip install pyvjoy

Axis mapping:
  vJoy Device 1, Axis X  ← flight stick X (roll)
  vJoy Device 1, Axis Y  ← flight stick Y (pitch)
  vJoy Device 1, Axis Z  ← throttle
  vJoy Device 1, Button 1 ← joystick trigger button
"""

from typing import Optional

try:
    import pyvjoy
    VJOY_AVAILABLE = True
except ImportError:
    VJOY_AVAILABLE = False

# vJoy axis value range: 1 to 32768
_VJOY_MIN = 0x0001
_VJOY_MAX = 0x8000
_VJOY_CENTER = (_VJOY_MIN + _VJOY_MAX) // 2


def _bipolar_to_vjoy(value: float) -> int:
    """Map -1.0 .. 1.0 to vJoy axis range."""
    clamped = max(-1.0, min(1.0, value))
    return int((clamped + 1.0) / 2.0 * (_VJOY_MAX - _VJOY_MIN) + _VJOY_MIN)


def _unipolar_to_vjoy(value: float) -> int:
    """Map 0.0 .. 1.0 to vJoy axis range."""
    clamped = max(0.0, min(1.0, value))
    return int(clamped * (_VJOY_MAX - _VJOY_MIN) + _VJOY_MIN)


class VJoyOutput:
    """
    Sends processed axis data to a vJoy virtual device.

    If vJoy is not installed, connect() returns False and send() is a no-op.
    """

    def __init__(self, device_id: int = 1):
        self._device_id = device_id
        self._device: Optional[object] = None

    def connect(self) -> bool:
        """Attempt to open the vJoy device. Returns True on success."""
        if not VJOY_AVAILABLE:
            return False
        try:
            self._device = pyvjoy.VJoyDevice(self._device_id)
            return True
        except Exception:
            return False

    def disconnect(self) -> None:
        self._device = None

    def is_available(self) -> bool:
        return VJOY_AVAILABLE and self._device is not None

    def send(self, x: float, y: float, throttle: float, button: bool) -> None:
        """
        Push axis values to the virtual joystick.

        Args:
            x:        Roll axis,    -1.0 (full left)  to  1.0 (full right)
            y:        Pitch axis,   -1.0 (full back)  to  1.0 (full forward)
            throttle: Throttle axis, 0.0 (idle)       to  1.0 (full power)
            button:   Trigger button state
        """
        if not self._device:
            return
        try:
            self._device.data.wAxisX = _bipolar_to_vjoy(x)
            self._device.data.wAxisY = _bipolar_to_vjoy(y)
            self._device.data.wAxisZ = _unipolar_to_vjoy(throttle)
            self._device.data.lButtons = 1 if button else 0
            self._device.update()
        except Exception:
            pass
