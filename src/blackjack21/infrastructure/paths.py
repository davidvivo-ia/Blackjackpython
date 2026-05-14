"""XDG-aware path resolution."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "blackjack21"


def data_dir() -> Path:
    """Return the canonical data directory for the app.

    Honours ``XDG_DATA_HOME`` on Linux/macOS and falls back to
    ``%LOCALAPPDATA%`` on Windows.
    """
    if sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA")
        base = (
            Path(local_appdata) if local_appdata else Path.home() / "AppData" / "Local"
        )
        return base / APP_NAME
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "share"
    return base / APP_NAME


def session_path(profile: str = "default") -> Path:
    """Path to the JSON file holding ``profile``'s saved session.

    The ``default`` profile keeps the legacy ``session.json`` location
    so users upgrading from v1.0 don't lose their bankroll. Named
    profiles get a dedicated file under ``profiles/<name>.json``.
    """
    if profile == "default":
        return data_dir() / "session.json"
    return data_dir() / "profiles" / f"{profile}.json"
