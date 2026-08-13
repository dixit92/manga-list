"""Tiny JSON config persistence (last folder, window size)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

if getattr(sys, "frozen", False):
    # PyInstaller one-file build: store data next to the exe (portable).
    _BASE_DIR = Path(sys.executable).resolve().parent
else:
    _BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG_PATH = _BASE_DIR / "data" / "config.json"

# Ensure the data directory exists.
CONFIG_PATH.parent.mkdir(exist_ok=True)

_DEFAULTS: Dict[str, Any] = {
    "last_root": "",
    "window": {"w": 1200, "h": 720},
    # List of absolute folder paths the user has marked as examined.
    "examined": [],
    # Whether to automatically start MU lookup after a scan.
    "mu_autostart": False,
    # Column names that are hidden by default.
    "hidden_columns": ["Vol %", "Ch %", "Both %"],
    # QHeaderView state as hex string — persists column order/widths.
    "column_state": "",
    # QSplitter sizes [left_px, right_px]; empty = use defaults.
    "splitter_sizes": [],
}


def load() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return dict(_DEFAULTS)
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(_DEFAULTS)
    merged = dict(_DEFAULTS)
    merged.update(data or {})
    # Ensure nested defaults
    win = dict(_DEFAULTS["window"])
    win.update(merged.get("window") or {})
    merged["window"] = win
    if not isinstance(merged.get("examined"), list):
        merged["examined"] = []
    if not isinstance(merged.get("hidden_columns"), list):
        merged["hidden_columns"] = list(_DEFAULTS["hidden_columns"])
    return merged


def save(cfg: Dict[str, Any]) -> None:
    try:
        CONFIG_PATH.write_text(
            json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        pass
