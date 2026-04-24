# Arduino Flight Controller

## Project Goal
A USB flight stick and throttle controller built from the Elegoo Super Starter Kit for UNO.
The Arduino UNO R3 reads physical inputs and sends serial data to a Python desktop app on
the PC, which translates them into virtual joystick inputs for use in flight simulation games
(DCS, MSFS, X-Plane, etc.).

## Hardware Components
| Component | Source | Role |
|-----------|--------|------|
| Arduino UNO R3 | Elegoo kit | Main controller board |
| Joystick module (KY-023) | Elegoo kit | X/Y flight stick axes + trigger button |
| Potentiometer (10 kΩ) | Elegoo kit | Throttle axis (integrated into 3D-printed throttle) |
| Jumper wires | Elegoo kit | Direct wiring (no breadboard) |

> The SG90 servo is not used. The potentiometer is the throttle position sensor.
> 0% and 100% endpoints are calibrated in software via the PC app.

## Wiring Diagram

### Joystick Module → Arduino UNO
| Joystick Pin | Arduino Pin | Notes |
|-------------|-------------|-------|
| GND | GND | |
| +5V | 5V | |
| VRx | A0 | X axis (roll) |
| VRy | A1 | Y axis (pitch) |
| SW | D2 | Button (active LOW, uses internal pullup) |

### Potentiometer (Throttle) → Arduino UNO (no breadboard)
| Pot Pin | Connection | Notes |
|---------|------------|-------|
| Left leg (GND) | Arduino GND | Use the second GND pin on the power header |
| Wiper (center) | Arduino A2 | Throttle reading |
| Right leg (VCC) | Joystick VCC pin | Daisy-chain off joystick — no breadboard needed |

> **No-breadboard wiring tip:** The Arduino power header has two GND pins and one 5V pin.
> Run the joystick GND to one GND pin and the pot GND to the other. For 5V, run a short
> wire from the pot's right leg directly to the joystick module's VCC pin, sharing power
> without a breadboard.
>
> **Power budget:** Joystick (~5 mA) + pot (~0.5 mA) = ~5.5 mA total. USB supplies 500 mA.
> No issues.

## Languages & Tools
- **C++ (Arduino)** — firmware in `firmware/flight_controller/flight_controller.ino`
- **Python 3** — configuration/output app in `app/`
- **Arduino IDE** — uploads firmware to the board
- **vJoy driver + pyvjoy** — creates a virtual joystick Windows can see

## Serial Protocol
The Arduino sends one CSV line at 50 Hz over USB serial (115200 baud):
```
X,Y,BTN,THROTTLE\n
```
| Field | Range | Description |
|-------|-------|-------------|
| X | 0–1023 | Joystick X axis (center ≈ 512) |
| Y | 0–1023 | Joystick Y axis (center ≈ 512) |
| BTN | 0 or 1 | Joystick button (1 = pressed) |
| THROTTLE | 0–1023 | Potentiometer position |

## Required Software (Windows)

### 1. Arduino IDE
Download: https://www.arduino.cc/en/software
Used to compile and upload `flight_controller.ino` to the UNO R3.

### 2. vJoy Driver
Download: https://sourceforge.net/projects/vjoystick/
- Run the installer, keep defaults
- Open **vJoy Configure** from Start menu
- Enable Device 1, check axes: X, Y, Z (for throttle)
- Enable at least 1 button
- Click Apply

### 3. Python 3
Download: https://www.python.org/downloads/ (3.10+ recommended)
During install, check "Add Python to PATH".

## Build & Run Instructions

### Upload Firmware
1. Open Arduino IDE
2. File → Open → navigate to `firmware/flight_controller/flight_controller.ino`
3. Tools → Board → Arduino UNO
4. Tools → Port → select the COM port for your Arduino (e.g. COM3)
5. Click Upload (→)

### Install Python Dependencies
```
cd app
pip install -r requirements.txt
```

### Run the Configuration App
```
cd app
python main.py
```

1. Select the Arduino COM port from the dropdown
2. Click **Connect**
3. Move the joystick — the X/Y bars should respond
4. Move the throttle to its physical **idle (0%)** position, then click **Set 0%** in the Throttle panel
5. Move the throttle to its physical **full (100%)** position, then click **Set 100%**
6. Verify the throttle bar and % readout span the full range with no dead areas
7. Adjust sensitivity and deadzone sliders as needed
8. Click **Save Config** to persist calibration to disk
9. Launch your flight sim — configure it to use vJoy Device 1 axes (X=roll, Y=pitch, Z=throttle)

> Calibration is stored in `config/default_config.json`. Re-run calibration any time the
> throttle feels off (e.g., after reassembling the 3D-printed mechanism).

## File Structure
```
arduino-flight-controller/
├── CLAUDE.md                  ← this file
├── todos.md                   ← task tracking
├── firmware/
│   └── flight_controller/
│       └── flight_controller.ino
├── app/
│   ├── main.py                ← GUI app (run this)
│   ├── serial_reader.py       ← Arduino serial parser
│   ├── vjoy_output.py         ← vJoy virtual joystick output
│   ├── config_manager.py      ← JSON config load/save
│   └── requirements.txt
└── config/
    └── default_config.json    ← saved settings
```
