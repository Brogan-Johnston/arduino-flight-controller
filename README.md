# Arduino Flight Stick & Throttle Controller

A USB flight stick and throttle controller built from the **Elegoo Super Starter Kit for UNO**.
The Arduino UNO R3 reads physical inputs and sends serial data to a Python desktop app on the
PC, which translates them into virtual joystick inputs for use in flight simulation games
(DCS World, Microsoft Flight Simulator, X-Plane, etc.).

---

## Table of Contents

1. [Hardware Components](#1-hardware-components)
2. [Wiring](#2-wiring)
3. [Required Software](#3-required-software)
4. [Hardware Setup](#4-hardware-setup)
5. [Uploading the Firmware](#5-uploading-the-firmware)
6. [Installing Python Dependencies](#6-installing-python-dependencies)
7. [Running the Config App](#7-running-the-config-app)
8. [Using the App](#8-using-the-app)
9. [Configuring Your Flight Sim](#9-configuring-your-flight-sim)
10. [Troubleshooting](#10-troubleshooting)
11. [File Structure](#11-file-structure)
12. [How It Works](#12-how-it-works)

---

## 1. Hardware Components

All components come from the Elegoo Super Starter Kit for UNO.

| Component | Kit Part | Role |
|-----------|----------|------|
| Arduino UNO R3 | Included | Main controller board |
| Joystick module (KY-023) | Included | X/Y flight stick axes + trigger button |
| Potentiometer (10 kΩ) | Included | Throttle position sensor (integrated into 3D-printed throttle) |
| Jumper wires (M-to-M) | Included | Direct wiring — no breadboard required |
| USB A-to-B cable | Included | Arduino ↔ PC |

> The SG90 servo is not used in this build. Throttle position is read from the
> potentiometer; the 0% and 100% endpoints are calibrated in the PC app.

---

## 2. Wiring

All components connect to the Arduino with jumper wires. A mini breadboard acts as a
5V power junction so both the joystick module and potentiometer can share the Arduino's
single 5V pin without needing to daisy-chain wires between components.

### Overview

```
Arduino UNO R3
  Power header (left side):
    5V  ──────────────────── Mini breadboard row 1 ─┬─ Joystick VCC
                                                    └─ Pot right leg (VCC)
    GND (pin 1 of 2) ─────── Joystick GND
    GND (pin 2 of 2) ─────── Pot left leg (GND)

  Analog header (right side):
    A0 ────────────────────── Joystick VRx
    A1 ────────────────────── Joystick VRy
    A2 ────────────────────── Pot wiper (center leg)

  Digital pin:
    D2 ────────────────────── Joystick SW
```

### Joystick Module (KY-023) → Arduino UNO

The joystick module has 5 pins along one edge, labelled on the PCB.

| Joystick Pin | Arduino Pin | Notes |
|-------------|-------------|-------|
| GND | GND (power header, first GND pin) | |
| +5V | 5V (power header) | |
| VRx | A0 | Left/right axis (roll) |
| VRy | A1 | Forward/back axis (pitch) |
| SW | D2 | Trigger button — active LOW |

> The button pin uses the Arduino's internal pull-up resistor, so no external resistor is needed.

### Potentiometer (Throttle) → Arduino UNO

The pot is integrated into the 3D-printed throttle mechanism. Its 5V power comes from
the mini breadboard junction shared with the joystick module.

| Potentiometer Pin | Connection | Notes |
|------------------|------------|-------|
| Left outer leg (GND) | Arduino GND (power header, second GND pin) | |
| Center wiper | Arduino A2 | Throttle position reading |
| Right outer leg (VCC) | Mini breadboard row 1 | Shares 5V with joystick via breadboard |

### Mini Breadboard Power Junction

The Arduino UNO has only one 5V pin on its power header. The mini breadboard acts as a
splitter so both the joystick and potentiometer can draw from it.

A 17x10 mini breadboard has no dedicated power rails — all 5 holes in the same row on
the same side of the center divider are connected. Use any free row as your 5V junction:

| Breadboard hole | Wire |
|----------------|------|
| Row 1, col a | Arduino 5V (from power header) |
| Row 1, col b | Joystick VCC pin |
| Row 1, col c | Potentiometer right outer leg (VCC) |

All three holes share the same connection, so 5V reaches both components from the single
Arduino 5V pin. Keep all three wires on the **same side** of the center divider.

> **Power budget:** Joystick (~5 mA) + potentiometer (~0.5 mA) = ~5.5 mA total.
> The Arduino's 5V rail supplies up to 500 mA via USB — no issues.

> **Arduino power header pin order** (from the reset button end):
> `RESET — 3.3V — 5V — GND — GND — VIN`
> Use the two GND pins to give the joystick and potentiometer each their own GND wire.

---

## 3. Required Software

Install these four things in order on your Windows PC before doing anything else.

### 3.1 Arduino IDE

Used to compile and upload the flight controller firmware to the UNO R3.

**Download:** https://www.arduino.cc/en/software

1. Click **Windows Win 10 and newer, 64 bits** (or the MSI installer).
2. Run the installer with default settings.
3. Allow the driver installation prompts — these let Windows recognize the UNO over USB.

### 3.2 vJoy Driver

vJoy creates a virtual joystick device that Windows and games can see, even though no physical
joystick is plugged in. The Python app feeds your Arduino data into this virtual device.

**Download:** https://sourceforge.net/projects/vjoystick/

1. Click **Download** and run the installer with default settings.
2. After installation, open **Configure vJoy** from the Start menu.
3. Under **Device 1**, make sure the following are checked:
   - Axis **X** (flight stick left/right)
   - Axis **Y** (flight stick forward/back)
   - Axis **Z** (throttle)
   - **Number of Buttons:** at least **1**
4. Click **Apply** and close the window.

> If you do not see "Configure vJoy" in the Start menu, look for **vJoyConf** inside
> `C:\Program Files\vJoy\x64\`.

### 3.3 Python 3

The configuration app is written in Python.

**Download:** https://www.python.org/downloads/ (version 3.10 or newer recommended)

1. Run the installer.
2. On the first screen, **check the box that says "Add Python to PATH"** before clicking Install.
3. Complete the installation.
4. Verify it worked: open a Command Prompt and type `python --version`. You should see a version number.

### 3.4 Python Packages

Once Python is installed, open a Command Prompt, navigate to the project's `app` folder,
and run:

```
pip install -r requirements.txt
```

This installs:
- **pyserial** — reads the Arduino's USB serial data
- **pyvjoy** — sends axis data to the vJoy virtual device

---

## 4. Hardware Setup

1. Place the Arduino UNO, joystick module, and potentiometer on your desk.
2. Connect all components directly to the Arduino according to the wiring tables in
   [Section 2](#2-wiring). No breadboard is needed.
3. Run a short jumper wire from the potentiometer's right leg (VCC) to the joystick
   module's VCC pin — this daisy-chains power between the two components.
4. Do not connect the Arduino to the PC yet — wait until after uploading firmware.

---

## 5. Uploading the Firmware

1. Open **Arduino IDE**.
2. Go to **File → Open** and navigate to:
   ```
   school/arduino-flight-controller/firmware/flight_controller/flight_controller.ino
   ```
3. Go to **Tools → Board** and select **Arduino Uno**.
4. Connect the Arduino to your PC via USB.
5. Go to **Tools → Port** and select the port labelled something like **COM3 (Arduino Uno)**.
   - If you are unsure which COM port, check Device Manager under **Ports (COM & LPT)**.
6. Click the **Upload** button (the right-arrow icon, or press `Ctrl+U`).
7. Wait for the IDE to show **Done uploading** in the status bar.
8. Open **Tools → Serial Monitor**, set the baud rate to **115200**, and confirm you see
   comma-separated numbers updating roughly 50 times per second:
   ```
   512,510,0,342
   512,511,0,344
   ```
   The four values are: joystick X, joystick Y, button (0 or 1), throttle raw ADC.
   Move the joystick and throttle to confirm all four values change. This confirms the
   firmware is running correctly.

> **Note:** The firmware no longer drives a servo. D9 is unused. If you previously had a
> servo connected to D9, disconnect it — it will not do anything and is not needed.

---

## 6. Installing Python Dependencies

Open a Command Prompt and run:

```
cd C:\Users\Broga\Projects\school\arduino-flight-controller\app
pip install -r requirements.txt
```

Expected output: pip downloads and installs `pyserial` and `pyvjoy` without errors.

---

## 7. Running the Config App

With the Arduino plugged in and firmware uploaded, double-click **`launch.bat`** in the
project root. It will:

1. Verify Python is installed (and tell you how to fix it if not)
2. Install or update the required Python packages automatically
3. Confirm the vJoy driver is present
4. Launch the app

This works the same for a first-time setup and for restarting the app on a return visit —
just double-click `launch.bat` every time.

> **Manual alternative:** if you prefer the command line:
> ```
> cd C:\Users\Broga\Projects\school\arduino-flight-controller\app
> python main.py
> ```

> **Common issue — "PermissionError: Access is denied" on COM3:**
> This means another program has the serial port open. The most likely cause is the
> Arduino IDE Serial Monitor still running from Step 5. Close the Serial Monitor (or
> Arduino IDE entirely) before running the app — only one program can hold the port at a time.

---

## 8. Using the App

### Connecting to the Arduino

1. In the **Port** dropdown, select the COM port your Arduino is on (e.g. `COM3`).
   - Click **Refresh** if the port is not listed.
2. Click **Connect**.
3. The status label turns green and shows **Connected**.
4. The **Live Input** panel on the right will start showing values as you move the stick and throttle.

### Sensitivity

Controls how aggressively the axis responds. The slider applies a **power curve**:

- **1.0** — linear, full 1:1 response across the whole range.
- **> 1.0** — less sensitive near center, more sensitive near the edges. Good for precise
  aiming in combat sims.
- **< 1.0** — more sensitive near center.

Adjust and watch the live bars to feel the difference.

### Deadzone

The fraction of the axis travel near center that is ignored and mapped to exactly zero.
Prevents stick drift from a loose joystick returning slightly off-center.

- **0%** — no deadzone (every tiny movement registers).
- **5–10%** — typical starting point.
- **Up to 50%** — use only if the stick is very drifty.

### Invert Axis

Flips the axis direction. Use this if your pitch or roll is backwards in-game.

### Joystick Center Calibration (Set Center)

If your joystick drifts slightly from the electrical center of 512:

1. Let go of the stick so it rests at neutral.
2. Click **Set Center** for the X axis and then the Y axis.
3. The app records the current raw reading as the center point for each axis.

### Throttle Calibration (Set 0% / Set 100%)

The throttle potentiometer rarely spans the full 0–1023 ADC range when integrated into
a physical throttle mechanism. Calibration tells the app exactly where your throttle's
physical idle and full-power stops are.

**Steps (do this once after assembly, and again after any mechanical changes):**

1. Connect to the Arduino and confirm the throttle bar is responding.
2. Move the throttle to its **physical idle (0%) stop** — the fully-back position.
3. Click **Set 0%** in the Throttle panel. The app stores that raw ADC value as the idle endpoint.
4. Move the throttle to its **physical full-power (100%) stop** — the fully-forward position.
5. Click **Set 100%**. The app stores that value as the full-power endpoint.
6. Slide the throttle from stop to stop and confirm:
   - The progress bar sweeps the full width.
   - The percentage readout next to the bar goes from **0%** to **100%**.
7. Click **Save Config** to persist the calibration.

> If you click **Set 100%** before **Set 0%**, or with the throttle in the wrong position,
> the app will warn you. Just repeat the steps in order.

### Saving Your Config

Click **Save Config** to write all settings (calibration, deadzone, sensitivity, invert)
to `config/default_config.json`. They load automatically the next time you open the app.

---

## 9. Configuring Your Flight Sim

The app outputs to **vJoy Device 1**. Each flight sim has its own controls menu —
look for joystick or HOTAS binding options and assign:

| vJoy Axis | Physical Control | Typical In-Game Binding |
|-----------|-----------------|------------------------|
| Axis X | Joystick left/right | Roll |
| Axis Y | Joystick forward/back | Pitch |
| Axis Z | Throttle potentiometer | Throttle |
| Button 1 | Joystick push-button | Weapons / fire / action |

**DCS World:** Options → Controls → select your aircraft → Axis Assign tab → click a binding
and move the physical input to auto-detect.

**Microsoft Flight Simulator:** Options → Controls → select vJoy Device → assign axes and
buttons as needed.

**X-Plane:** Settings → Joystick → select vJoy Device → drag axes to the desired function.

---

## 10. Troubleshooting

### "Port not listed / cannot connect"
- Make sure the Arduino is plugged in via USB.
- Click **Refresh** in the app.
- Check Device Manager → Ports (COM & LPT) to confirm Windows sees the Arduino.
- If it shows as an unknown device, re-install the Arduino IDE drivers.

### Live display does not respond / all zeros
- Open Arduino IDE Serial Monitor (115200 baud) to confirm the firmware is sending data.
- Make sure only one program (Serial Monitor OR the Python app) is connected to the port at
  a time — they cannot both be open simultaneously.

### "vJoy: Not found" in the app
- Install the vJoy driver (see Section 3.2).
- After installing, restart the app.

### vJoy Device 1 not visible in games
- Open **Configure vJoy**, confirm Device 1 is enabled with axes X, Y, Z and at least 1 button, and click Apply.
- Check Windows **Control Panel → Devices and Printers** — vJoy Device should appear there.

### Throttle shows 0% or 100% at rest / calibration feels off
- Re-run throttle calibration: move to the physical idle stop → **Set 0%**, move to full stop → **Set 100%**, then **Save Config**.
- Check that the potentiometer wiper wire is firmly seated in A2 and that the pot's legs have good contact with the VCC daisy-chain wire and the GND pin.

### Axis is reversed in-game
- Check the **Invert** checkbox for that axis in the app, or use the in-game axis invert option.

### Joystick drifts at rest
- Increase the **Deadzone** slider for that axis.
- Click **Set Center** with the stick at rest to update the neutral reference point.

---

## 11. File Structure

```
arduino-flight-controller/
├── README.md                       ← this file
├── CLAUDE.md                       ← project notes for Claude Code
├── todos.md                        ← task tracking
├── launch.bat                      ← double-click to set up and run the app
│
├── firmware/
│   └── flight_controller/
│       └── flight_controller.ino   ← upload this to the Arduino
│
├── app/
│   ├── main.py                     ← run this to open the config app
│   ├── serial_reader.py            ← reads and parses Arduino serial data
│   ├── vjoy_output.py              ← sends processed axes to vJoy
│   ├── config_manager.py           ← loads and saves JSON config
│   └── requirements.txt            ← pip install -r requirements.txt
│
└── config/
    └── default_config.json         ← saved sensitivity/deadzone settings
```

---

## 12. How It Works

```
Physical inputs
    │
    ▼
Arduino UNO R3
  • Reads joystick X (A0), Y (A1), button (D2) at 50 Hz
  • Reads throttle potentiometer (A2) — raw ADC 0–1023
  • Sends:  X,Y,BTN,THROTTLE  over USB serial at 115200 baud
    │
    ▼  USB cable
Python app  (main.py)
  • serial_reader.py   parses the CSV stream in a background thread
  • config_manager.py  holds calibration endpoints, deadzone, sensitivity, invert
  • main.py            maps raw throttle ADC through calibrated 0%–100% range,
                       applies deadzone and sensitivity curves,
                       updates the live display at 50 Hz
  • vjoy_output.py     pushes the processed axes to vJoy Device 1
    │
    ▼  Windows driver
vJoy Device 1
  (appears as a standard joystick to any game or sim)
```

The Arduino sends raw ADC values (0–1023). The Python app normalises the stick axes to
-1.0 → +1.0 and maps the throttle through your calibrated endpoints to 0.0 → 1.0, then
applies deadzone and sensitivity before forwarding to vJoy.

Throttle calibration is stored in `config/default_config.json` as the `min` and `max`
values for the throttle axis. No firmware changes are needed when you recalibrate.
