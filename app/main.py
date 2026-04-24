"""
main.py  —  Flight Controller Configuration App

Run with:  python main.py

This app:
  1. Connects to the Arduino over USB serial
  2. Reads joystick X/Y and throttle data
  3. Applies deadzone and sensitivity from on-screen sliders
  4. Outputs the processed axes to a vJoy virtual joystick
  5. Shows a live display of current axis positions

Requires: pyserial, pyvjoy (and the vJoy Windows driver)
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from copy import deepcopy

import serial.tools.list_ports

# Make sure local modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from serial_reader import SerialReader, ControllerState
from vjoy_output import VJoyOutput, VJOY_AVAILABLE
from config_manager import ConfigManager, DEFAULT_CONFIG


# ── Axis math helpers ──────────────────────────────────────────────────────

def _apply_deadzone(value: float, deadzone: float) -> float:
    """
    Shrink a -1..1 value so the dead band around zero maps to exactly 0,
    then re-scale the remaining range back to -1..1.
    """
    if deadzone <= 0.0:
        return value
    if abs(value) < deadzone:
        return 0.0
    sign = 1.0 if value > 0 else -1.0
    return sign * (abs(value) - deadzone) / (1.0 - deadzone)


def _apply_sensitivity(value: float, sensitivity: float) -> float:
    """
    Power curve: sensitivity > 1 makes the stick less responsive near center
    and more responsive near the edges (good for fine aiming).
    sensitivity = 1.0 → linear (no change).
    """
    if sensitivity == 1.0:
        return value
    sign = 1.0 if value >= 0 else -1.0
    return sign * (abs(value) ** (1.0 / max(sensitivity, 0.01)))


def normalize_bipolar(raw: int, cfg: dict) -> float:
    """
    Map a raw ADC value (0–1023) for a centered axis (joystick X or Y)
    to the range -1.0 .. 1.0, then apply deadzone, sensitivity, and invert.
    """
    mn = cfg["min"]
    mx = cfg["max"]
    center = cfg["center"]

    if raw <= center:
        val = -(center - raw) / max(center - mn, 1)
    else:
        val = (raw - center) / max(mx - center, 1)

    val = max(-1.0, min(1.0, val))

    if cfg.get("inverted"):
        val = -val

    val = _apply_deadzone(val, cfg["deadzone"])
    val = _apply_sensitivity(val, cfg["sensitivity"])
    return val


def normalize_unipolar(raw: int, cfg: dict) -> float:
    """
    Map a raw ADC value (0–1023) for the throttle axis to 0.0 .. 1.0,
    then apply deadzone, sensitivity, and invert.
    """
    mn = cfg["min"]
    mx = cfg["max"]

    val = (raw - mn) / max(mx - mn, 1)
    val = max(0.0, min(1.0, val))

    if cfg.get("inverted"):
        val = 1.0 - val

    dz = cfg.get("deadzone", 0.0)
    if dz > 0.0:
        if val < dz:
            val = 0.0
        else:
            val = (val - dz) / (1.0 - dz)

    val = _apply_sensitivity(val, cfg["sensitivity"])
    return val


# ── Main application ───────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Flight Controller Config")
        self.resizable(False, False)

        self._cfg = ConfigManager()
        self._cfg.load()

        self._reader: SerialReader | None = None
        self._vjoy = VJoyOutput()
        self._vjoy_ok = self._vjoy.connect()

        self._state = ControllerState()
        self._lock = threading.Lock()

        self._build_ui()
        self._load_ui_from_config()
        self._refresh_ports()

        # Start the 50ms display refresh loop
        self.after(50, self._tick)

    # ── UI construction ────────────────────────────────────────────────

    def _build_ui(self) -> None:
        p = {"padx": 8, "pady": 4}

        # Connection bar
        conn = ttk.LabelFrame(self, text="Connection")
        conn.grid(row=0, column=0, columnspan=2, sticky="ew", **p)
        self._build_connection_bar(conn)

        # Axis config (left column)
        self._axis_widgets: dict[str, dict] = {}
        axes_col = ttk.Frame(self)
        axes_col.grid(row=1, column=0, sticky="nsew", **p)
        for idx, (name, title) in enumerate([
            ("x",        "X Axis  (Roll / Left–Right)"),
            ("y",        "Y Axis  (Pitch / Forward–Back)"),
            ("throttle", "Throttle"),
        ]):
            self._axis_widgets[name] = self._build_axis_panel(axes_col, name, title, idx)

        # Live display (right column)
        live = ttk.LabelFrame(self, text="Live Input")
        live.grid(row=1, column=1, sticky="nsew", padx=8, pady=4)
        self._build_live_panel(live)

        # Bottom buttons
        btns = ttk.Frame(self)
        btns.grid(row=2, column=0, columnspan=2, pady=6)
        ttk.Button(btns, text="Save Config",    command=self._save_config   ).pack(side="left", padx=4)
        ttk.Button(btns, text="Load Config",    command=self._load_config   ).pack(side="left", padx=4)
        ttk.Button(btns, text="Reset Defaults", command=self._reset_defaults).pack(side="left", padx=4)

    def _build_connection_bar(self, parent: tk.Widget) -> None:
        p = {"padx": 6, "pady": 4}
        ttk.Label(parent, text="Port:").grid(row=0, column=0, **p)

        self._port_var = tk.StringVar()
        self._port_combo = ttk.Combobox(parent, textvariable=self._port_var, width=10, state="readonly")
        self._port_combo.grid(row=0, column=1, **p)

        ttk.Button(parent, text="Refresh", command=self._refresh_ports).grid(row=0, column=2, **p)

        self._conn_btn = ttk.Button(parent, text="Connect", command=self._toggle_connection)
        self._conn_btn.grid(row=0, column=3, **p)

        self._status_lbl = ttk.Label(parent, text="Disconnected", foreground="red", width=14)
        self._status_lbl.grid(row=0, column=4, **p)

        vjoy_text  = "vJoy: Ready" if self._vjoy_ok else "vJoy: Not found — install driver"
        vjoy_color = "green"       if self._vjoy_ok else "orange"
        ttk.Label(parent, text=vjoy_text, foreground=vjoy_color).grid(row=0, column=5, **p)

    def _build_axis_panel(self, parent: tk.Widget, axis: str, title: str, row: int) -> dict:
        frame = ttk.LabelFrame(parent, text=title)
        frame.grid(row=row, column=0, sticky="ew", padx=4, pady=4)
        frame.columnconfigure(1, weight=1)
        p = {"padx": 6, "pady": 3}
        w: dict = {}

        # Sensitivity slider
        ttk.Label(frame, text="Sensitivity:").grid(row=0, column=0, sticky="e", **p)
        sens_var = tk.DoubleVar(value=1.0)
        ttk.Scale(frame, from_=0.1, to=3.0, variable=sens_var,
                  orient="horizontal", length=200).grid(row=0, column=1, **p)
        sens_lbl = ttk.Label(frame, text="1.00", width=5)
        sens_lbl.grid(row=0, column=2, **p)
        sens_var.trace_add("write", lambda *_: sens_lbl.config(text=f"{sens_var.get():.2f}"))
        w["sensitivity"] = sens_var

        # Deadzone slider
        ttk.Label(frame, text="Deadzone:").grid(row=1, column=0, sticky="e", **p)
        dz_var = tk.DoubleVar(value=0.05)
        ttk.Scale(frame, from_=0.0, to=0.50, variable=dz_var,
                  orient="horizontal", length=200).grid(row=1, column=1, **p)
        dz_lbl = ttk.Label(frame, text=" 5%", width=5)
        dz_lbl.grid(row=1, column=2, **p)
        dz_var.trace_add("write", lambda *_: dz_lbl.config(text=f"{dz_var.get()*100:3.0f}%"))
        w["deadzone"] = dz_var

        # Invert checkbox + calibrate button(s)
        inv_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="Invert axis", variable=inv_var).grid(
            row=2, column=1, sticky="w", **p)
        w["inverted"] = inv_var

        if axis == "throttle":
            ttk.Button(
                frame, text="Set 0%",
                command=self._set_throttle_min,
            ).grid(row=2, column=2, **p)
            ttk.Button(
                frame, text="Set 100%",
                command=self._set_throttle_max,
            ).grid(row=3, column=2, **p)
        else:
            ttk.Button(
                frame, text="Set Center",
                command=lambda a=axis: self._set_center(a),
            ).grid(row=2, column=2, **p)

        return w

    def _build_live_panel(self, parent: tk.Widget) -> None:
        p = {"padx": 10, "pady": 6}
        self._bars: dict[str, ttk.Progressbar] = {}
        self._raw_labels: dict[str, tk.StringVar] = {}

        rows = [("x", "X (Roll)"), ("y", "Y (Pitch)"), ("throttle", "Throttle")]
        for idx, (axis, label) in enumerate(rows):
            ttk.Label(parent, text=label + ":", width=12, anchor="e").grid(
                row=idx, column=0, **p)

            bar = ttk.Progressbar(parent, length=170, maximum=200, mode="determinate")
            bar.grid(row=idx, column=1, **p)
            self._bars[axis] = bar

            rv = tk.StringVar(value="–")
            ttk.Label(parent, textvariable=rv, width=10).grid(row=idx, column=2, **p)
            self._raw_labels[axis] = rv

        self._btn_lbl_var = tk.StringVar(value="TRIGGER: off")
        ttk.Label(parent, textvariable=self._btn_lbl_var,
                  font=("", 10, "bold")).grid(row=3, column=0, columnspan=3, pady=8)

    # ── Config helpers ────────────────────────────────────────────────

    def _load_ui_from_config(self) -> None:
        for axis in ("x", "y", "throttle"):
            cfg = self._cfg.get_axis(axis)
            w = self._axis_widgets[axis]
            w["sensitivity"].set(cfg.get("sensitivity", 1.0))
            w["deadzone"].set(cfg.get("deadzone", 0.05))
            w["inverted"].set(cfg.get("inverted", False))
        self._port_var.set(self._cfg.config.get("serial_port", "COM3"))

    def _push_ui_to_config(self) -> None:
        for axis in ("x", "y", "throttle"):
            w = self._axis_widgets[axis]
            self._cfg.set_axis(axis, "sensitivity", round(w["sensitivity"].get(), 3))
            self._cfg.set_axis(axis, "deadzone",    round(w["deadzone"].get(),    3))
            self._cfg.set_axis(axis, "inverted",    w["inverted"].get())
        self._cfg.config["serial_port"] = self._port_var.get()

    def _save_config(self) -> None:
        self._push_ui_to_config()
        ok = self._cfg.save()
        if ok:
            messagebox.showinfo("Saved", "Configuration saved to disk.")
        else:
            messagebox.showerror("Error", "Could not write config file.")

    def _load_config(self) -> None:
        ok = self._cfg.load()
        if ok:
            self._load_ui_from_config()
            messagebox.showinfo("Loaded", "Configuration loaded from disk.")
        else:
            messagebox.showerror("Error", "Config file not found. Using defaults.")

    def _reset_defaults(self) -> None:
        self._cfg.config["axes"] = deepcopy(DEFAULT_CONFIG["axes"])
        self._load_ui_from_config()

    # ── Serial connection ─────────────────────────────────────────────

    def _refresh_ports(self) -> None:
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self._port_combo["values"] = ports
        if ports and not self._port_var.get():
            self._port_var.set(ports[0])

    def _toggle_connection(self) -> None:
        if self._reader and self._reader.is_connected():
            self._reader.disconnect()
            self._reader = None
            self._conn_btn.config(text="Connect")
            self._status_lbl.config(text="Disconnected", foreground="red")
            return

        port = self._port_var.get()
        if not port:
            messagebox.showerror("No Port", "Select a COM port from the dropdown.")
            return

        baud = self._cfg.config.get("baud_rate", 115200)
        self._reader = SerialReader(port, baud, self._on_data)
        try:
            self._reader.connect()
            self._conn_btn.config(text="Disconnect")
            self._status_lbl.config(text="Connected", foreground="green")
        except Exception as exc:
            messagebox.showerror("Connection Error", str(exc))
            self._reader = None

    # ── Data callback (runs in reader thread) ─────────────────────────

    def _on_data(self, state: ControllerState) -> None:
        with self._lock:
            self._state = state

    # ── Calibration ───────────────────────────────────────────────────

    def _set_center(self, axis: str) -> None:
        """Record the current raw reading as the center/neutral position."""
        with self._lock:
            raw = self._state.x if axis == "x" else self._state.y
        self._cfg.set_axis(axis, "center", raw)
        messagebox.showinfo("Center Set", f"{axis.upper()} center locked to raw {raw}.")

    def _set_throttle_min(self) -> None:
        """Lock the current throttle position as the 0% endpoint."""
        with self._lock:
            raw = self._state.throttle
        self._cfg.set_axis("throttle", "min", raw)
        messagebox.showinfo("Throttle 0% Set",
                            f"0% position locked to raw ADC {raw}.\n"
                            "Click Save Config to persist.")

    def _set_throttle_max(self) -> None:
        """Lock the current throttle position as the 100% endpoint."""
        with self._lock:
            raw = self._state.throttle
        mx = self._cfg.get_axis("throttle").get("min", 0)
        if raw <= mx:
            messagebox.showwarning("Bad Calibration",
                                   f"Raw value {raw} is not greater than the 0% value ({mx}).\n"
                                   "Move the throttle to its full-forward position first.")
            return
        self._cfg.set_axis("throttle", "max", raw)
        messagebox.showinfo("Throttle 100% Set",
                            f"100% position locked to raw ADC {raw}.\n"
                            "Click Save Config to persist.")

    # ── 50 Hz display tick (runs in main thread) ──────────────────────

    def _tick(self) -> None:
        with self._lock:
            state = self._state

        # Read current slider values into config so changes take effect live
        self._push_ui_to_config()

        # Normalise
        x = normalize_bipolar(state.x, self._cfg.get_axis("x"))
        y = normalize_bipolar(state.y, self._cfg.get_axis("y"))
        t = normalize_unipolar(state.throttle, self._cfg.get_axis("throttle"))

        # Update progress bars
        # X and Y: map -1..1 → 0..200 (center at 100)
        self._bars["x"]["value"]        = (x + 1.0) * 100.0
        self._bars["y"]["value"]        = (y + 1.0) * 100.0
        self._bars["throttle"]["value"] = t * 200.0

        # Update raw readouts
        self._raw_labels["x"].set(f"raw {state.x:4d}")
        self._raw_labels["y"].set(f"raw {state.y:4d}")
        self._raw_labels["throttle"].set(f"raw {state.throttle:4d}  ({t*100:.0f}%)")

        # Button indicator
        self._btn_lbl_var.set("TRIGGER: ON" if state.button else "TRIGGER: off")

        # Push to vJoy
        if self._vjoy_ok:
            self._vjoy.send(x, y, t, state.button)

        self.after(50, self._tick)


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
