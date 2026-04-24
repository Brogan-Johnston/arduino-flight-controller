"""
config_manager.py

Loads and saves the flight controller configuration as JSON.
Config file location: ../config/default_config.json (relative to this file).

Config schema:
{
  "serial_port": "COM3",
  "baud_rate": 115200,
  "axes": {
    "x":        { "min", "max", "center", "deadzone", "sensitivity", "inverted" },
    "y":        { "min", "max", "center", "deadzone", "sensitivity", "inverted" },
    "throttle": { "min", "max",           "deadzone", "sensitivity", "inverted" }
  }
}

Axis notes:
  - x, y have a "center" key because they are bipolar (output -1..1).
  - throttle has no "center" because it is unipolar (output 0..1).
  - deadzone: fraction of full range to ignore around center (or low end for throttle).
  - sensitivity: exponent for a power curve (>1 = less sensitive near center).
"""

import json
import os
from copy import deepcopy
from typing import Any

DEFAULT_CONFIG: dict = {
    "serial_port": "COM3",
    "baud_rate": 115200,
    "axes": {
        "x": {
            "min": 0,
            "max": 1023,
            "center": 512,
            "deadzone": 0.05,
            "sensitivity": 1.0,
            "inverted": False,
        },
        "y": {
            "min": 0,
            "max": 1023,
            "center": 512,
            "deadzone": 0.05,
            "sensitivity": 1.0,
            "inverted": False,
        },
        "throttle": {
            "min": 0,
            "max": 1023,
            "deadzone": 0.0,
            "sensitivity": 1.0,
            "inverted": False,
        },
    },
}

_DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "config", "default_config.json"
)


class ConfigManager:
    def __init__(self, path: str = _DEFAULT_PATH):
        self._path = os.path.abspath(path)
        self.config: dict = deepcopy(DEFAULT_CONFIG)

    # ── Persistence ───────────────────────────────────────────────────

    def load(self) -> bool:
        """Load config from disk. Returns True on success."""
        try:
            with open(self._path, "r") as f:
                loaded = json.load(f)
            self._deep_update(self.config, loaded)
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def save(self) -> bool:
        """Save current config to disk. Returns True on success."""
        try:
            os.makedirs(os.path.dirname(self._path), exist_ok=True)
            with open(self._path, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except OSError:
            return False

    # ── Axis helpers ──────────────────────────────────────────────────

    def get_axis(self, name: str) -> dict:
        return self.config["axes"].get(name, {})

    def set_axis(self, name: str, key: str, value: Any) -> None:
        self.config["axes"][name][key] = value

    # ── Internal ──────────────────────────────────────────────────────

    @staticmethod
    def _deep_update(base: dict, override: dict) -> None:
        """Recursively merge override into base (in place)."""
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                ConfigManager._deep_update(base[k], v)
            else:
                base[k] = v
