# lt_update.py — GitHub/HTTP update checker + staging (no external deps)
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from packaging.version import Version, InvalidVersion

import lt_core as core


@dataclass
class UpdateInfo:
    version: str
    notes: str
    url: str
    sha256: str


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_json(url: str, timeout: int = 10) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "SegLabUpdater/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw.decode("utf-8"))


def _platform_key() -> str:
    # map to latest.json keys
    if platform.system().lower().startswith("darwin"):
        return "mac"
    if platform.system().lower().startswith("windows"):
        return "win"
    return "linux"


def check_for_update(update_json_url: str, current_version: str) -> Optional[UpdateInfo]:
    data = _fetch_json(update_json_url)
    latest = str(data.get("version") or "").strip()
    notes = str(data.get("notes") or "").strip()

    try:
        if Version(latest) <= Version(current_version):
            return None
    except InvalidVersion:
        # if versions are weird, be conservative
        if latest == current_version:
            return None

    key = _platform_key()
    entry = data.get(key) or {}
    url = str(entry.get("url") or "").strip()
    sha = str(entry.get("sha256") or "").strip().lower()

    if not url:
        raise RuntimeError(f"latest.json does not contain a download URL for platform '{key}'.")
    if not sha or len(sha) < 32:
        raise RuntimeError("latest.json missing sha256 for the update file.")

    return UpdateInfo(version=latest, notes=notes, url=url, sha256=sha)


def download_update(info: UpdateInfo) -> Path:
    # stage into USER_WRITE_DIR/updates/
    updates_dir = Path(core.USER_WRITE_DIR) / "updates"
    updates_dir.mkdir(parents=True, exist_ok=True)

    # download to temp first
    fd, tmp = tempfile.mkstemp(prefix="seglab_update_", suffix=".zip")
    Path(tmp).unlink(missing_ok=True)

    req = urllib.request.Request(info.url, headers={"User-Agent": "SegLabUpdater/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)

    p = Path(tmp)
    got = _sha256_file(p)
    if got.lower() != info.sha256.lower():
        p.unlink(missing_ok=True)
        raise RuntimeError(f"SHA256 mismatch.\nExpected: {info.sha256}\nGot:      {got}")

    final = updates_dir / f"SegLabEPFL_{info.version}.zip"
    if final.exists():
        final.unlink()
    shutil.move(str(p), str(final))
    return final
