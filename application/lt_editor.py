from __future__ import annotations
import os, sys, subprocess
from pathlib import Path
from typing import Optional
import lt_core as core
from lt_utils import open_default

def itksnap_exec() -> Optional[Path]:
    if sys.platform == "darwin":
        for p in [
            Path("/Applications/ITK-SNAP.app/Contents/MacOS/ITK-SNAP"),
            Path("/Applications/ITK-SNAP.app/Contents/MacOS/itksnap"),
        ]:
            if p.exists():
                return p
    user = core.cfg_get("itksnap_path", "")
    if user:
        p = Path(str(user)).expanduser()
        if p.exists():
            return p
    return None

def launch(t1: Path, seg: Path) -> None:
    editor = core.cfg_get("editor", "itksnap")
    if editor == "itksnap":
        exe = itksnap_exec()
        if exe:
            try:
                subprocess.Popen([str(exe), "-g", str(t1), "-s", str(seg)])
                return
            except Exception:
                pass
    open_default(t1)
    open_default(seg)
