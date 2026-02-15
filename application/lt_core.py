from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

# =========================
# APP IDENTITY
# =========================
APP_NAME = "SegLab (EPFL)"
APP_VERSION = "1.0.1"

# =========================
# UPDATES (GitHub Releases)
# =========================
# The app's "Update" button should read this JSON (raw URL), which then points to the
# latest GitHub Release assets (mac/win zips). Keep this file in your repo:
# application/resources/update/latest.json
UPDATE_FEED_URL = (
    "https://raw.githubusercontent.com/fredericloboda/SegLab-EPFL/main/"
    "application/resources/update/latest.json"
)

# =========================
# BRAND / THEME
# =========================
EPFL_RED = "#e2001a"

# UI palette (dark)
BG0 = "#07080b"
PANEL = "#0f1218"
BG1 = PANEL  # alias for compatibility
PANEL2 = "#0b0d12"
STROKE = "#1d2230"
TEXT = "#e7e9f1"
MUTED = "#9aa3b2"
BTN = "#141a24"
BTN_H = "#1a2130"

# =========================
# PATHS
# =========================
APP_ROOT = Path(__file__).resolve().parent
RESOURCES = APP_ROOT / "resources"
PUBLIC_MATERIALS_DIR = RESOURCES / "materials_public"

USER_DATA = Path.home() / "SegLabEPFL_UserData"
CFG_PATH = USER_DATA / "config.json"

LOCAL_CASES = USER_DATA / "cases_local"
WORKSPACE = USER_DATA / "cases_workspace"
LOCAL_MATERIALS = USER_DATA / "materials_local"
LOCAL_PROGRESS = USER_DATA / "progress_local" / "attempts"
UPDATES_DIR = USER_DATA / "updates"

# =========================
# DEFAULTS
# =========================
DEFAULT_MIN_VOXELS = 10
DEFAULT_TOLERANCE = 150

# EPFL SMB share (for protected data; must be mounted by OS)
SMB_URL = "smb://sv-nas1.rcp.epfl.ch/Hummel-Lab"

def ensure_dirs() -> None:
    for p in (USER_DATA, LOCAL_CASES, WORKSPACE, LOCAL_MATERIALS, LOCAL_PROGRESS, UPDATES_DIR):
        p.mkdir(parents=True, exist_ok=True)

# =========================
# CONFIG
# =========================
def cfg_load() -> Dict[str, Any]:
    try:
        if CFG_PATH.exists():
            d = json.loads(CFG_PATH.read_text(encoding="utf-8"))
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}

def cfg_save(d: Dict[str, Any]) -> None:
    try:
        CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CFG_PATH.write_text(json.dumps(d, indent=2), encoding="utf-8")
    except Exception:
        pass

def cfg_get(k: str, default=None):
    return cfg_load().get(k, default)

def cfg_set(k: str, v) -> None:
    d = cfg_load()
    d[k] = v
    cfg_save(d)

# =========================
# LOCKED POLICY (classroom)
# =========================
_LOCKED_POLICY: dict | None = None  # runtime cache

def set_locked_policy(policy: dict | None) -> None:
    """Store classroom policy (min_voxels/tolerance/session) when joined to a class."""
    global _LOCKED_POLICY
    _LOCKED_POLICY = policy if isinstance(policy, dict) else None
    try:
        cfg_set("locked_policy", _LOCKED_POLICY)
    except Exception:
        pass

def get_locked_policy() -> dict | None:
    """Return classroom policy if present; otherwise None."""
    global _LOCKED_POLICY
    if isinstance(_LOCKED_POLICY, dict):
        return _LOCKED_POLICY
    try:
        p = cfg_get("locked_policy", None)
        if isinstance(p, dict):
            _LOCKED_POLICY = p
            return p
    except Exception:
        pass
    return None
