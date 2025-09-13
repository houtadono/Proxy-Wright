# paths.py
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from config import APP_NAME  # keep your existing config import


# ----------------------------
# Core helpers
# ----------------------------
def get_app_path() -> Path:
    """
    Directory of the executable when frozen, or the project root in dev.
    - Frozen (PyInstaller): folder that contains the .exe (onedir/onefile stub)
    - Dev: repo root (one level up from this file)
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_resource_root() -> Path:
    """
    Read-only resources root.
    - Frozen: sys._MEIPASS → dist/.../_internal (onedir) or temp (onefile)
    - Dev: same as get_app_path()
    Use this for bundled resources: translations/, bin/, themes/, etc.
    """
    return Path(getattr(sys, "_MEIPASS", get_app_path()))


def _is_writable(p: Path) -> bool:
    """
    Best-effort check: can we write here?
    Used to detect truly portable layout (user unzipped somewhere writable).
    """
    try:
        p.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryFile(dir=p):
            pass
        return True
    except Exception:
        return False


def is_portable_mode() -> bool:
    """
    Heuristics:
    - If a 'portable.flag' exists next to the exe → portable.
    - If the app folder is writable → portable (user unzipped it).
    Otherwise treat as installed (use OS-specific app-data).
    """
    app_dir = get_app_path()
    if (app_dir / "portable.flag").exists():
        return True
    return _is_writable(app_dir)


# ----------------------------
# Writable locations (user data)
# ----------------------------
def get_user_data_path() -> Path:
    """
    Writable data directory for DB, settings, logs, caches, Playwright browsers, etc.
    - Portable: ./Appdata next to the exe
    - Installed:
        * Windows: %LOCALAPPDATA%/<APP_NAME>
        * macOS:   ~/Library/Application Support/<APP_NAME>
        * Linux:   ~/.local/share/<APP_NAME>
    """
    if is_portable_mode():
        base = get_app_path() / "Appdata"
    else:
        if sys.platform.startswith("win"):
            base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support" / APP_NAME
        else:
            base = Path.home() / ".local" / "share" / APP_NAME

    base.mkdir(parents=True, exist_ok=True)
    return base


def get_setting_path() -> Path:
    """User settings file (writable)."""
    return get_user_data_path() / "settings.ini"


def get_database_path() -> Path:
    """SQLite DB file (writable)."""
    return get_user_data_path() / "profiles.db"


def get_profile_data_dir(profile_id: int) -> Path:
    """Per-profile writable directory."""
    p = get_user_data_path() / "profiles" / str(profile_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_logs_dir() -> Path:
    """Logs directory (writable)."""
    p = get_user_data_path() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_browsers_dir() -> Path:
    """
    Playwright browsers location (writable).
    Set PLAYWRIGHT_BROWSERS_PATH to this path before installing/launching.
    """
    p = get_user_data_path() / "browsers"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ----------------------------
# Read-only bundled resources
# ----------------------------
def get_translations_dir() -> Path:
    """
    Bundled translations (.qm) folder (read-only).
    NOTE:
      - Do NOT mkdir here when frozen; this is inside _internal.
      - In dev, the folder is your repo's translations/.
    """
    p = get_resource_root() / "translations"
    if not getattr(sys, "frozen", False):
        p.mkdir(parents=True, exist_ok=True)
    return p


def get_bin_dir() -> Path:
    """
    Bundled binaries folder (read-only), e.g. bin/3proxy.exe.
    Access-only; do not write here.
    """
    return get_resource_root() / "bin"


# ----------------------------
# Re-exports for convenience
# ----------------------------
BIN_DIR = get_bin_dir()
TRANS_DIR = get_translations_dir()
USER_DATA_DIR = get_user_data_path()
LOGS_DIR = get_logs_dir()
BROWSERS_DIR = get_browsers_dir()

__all__ = [
    "get_app_path",
    "get_resource_root",
    "is_portable_mode",
    "get_user_data_path",
    "get_setting_path",
    "get_database_path",
    "get_profile_data_dir",
    "get_logs_dir",
    "get_browsers_dir",
    "get_translations_dir",
    "get_bin_dir",
    "BIN_DIR",
    "TRANS_DIR",
    "USER_DATA_DIR",
    "LOGS_DIR",
    "BROWSERS_DIR",
]
