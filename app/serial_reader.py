"""
serial_reader.py

Background thread that reads CSV lines from the Arduino over USB serial
and calls a callback with a parsed ControllerState.

Expected serial format (115200 baud, 50 Hz):
    X,Y,BTN,THROTTLE\\n
    X, Y, THROTTLE: integers 0–1023
    BTN: 0 or 1
"""

import threading
from dataclasses import dataclass
from typing import Callable, Optional

import serial


@dataclass
class ControllerState:
    x: int = 512        # Joystick X, 0–1023 (center ≈ 512)
    y: int = 512        # Joystick Y, 0–1023 (center ≈ 512)
    button: bool = False
    throttle: int = 0   # Throttle, 0–1023


class SerialReader:
    """
    Opens a serial port in a background daemon thread and parses Arduino data.

    Usage:
        reader = SerialReader("COM3", 115200, callback)
        reader.connect()
        ...
        reader.disconnect()
    """

    def __init__(
        self,
        port: str,
        baud_rate: int,
        on_data: Callable[[ControllerState], None],
    ):
        self._port = port
        self._baud_rate = baud_rate
        self._on_data = on_data
        self._serial: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def connect(self) -> None:
        """Open the serial port and start the reading thread. Raises on failure."""
        self._serial = serial.Serial(self._port, self._baud_rate, timeout=1)
        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        """Stop reading and close the port."""
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()

    def is_connected(self) -> bool:
        return bool(
            self._serial
            and self._serial.is_open
            and self._running
        )

    def _read_loop(self) -> None:
        while self._running:
            try:
                raw = self._serial.readline()
                line = raw.decode("ascii", errors="ignore").strip()
                if not line:
                    continue

                parts = line.split(",")
                if len(parts) != 4:
                    continue

                state = ControllerState(
                    x=int(parts[0]),
                    y=int(parts[1]),
                    button=bool(int(parts[2])),
                    throttle=int(parts[3]),
                )
                self._on_data(state)

            except ValueError:
                # Malformed packet — skip
                continue
            except serial.SerialException:
                # Port disconnected
                self._running = False
                break
