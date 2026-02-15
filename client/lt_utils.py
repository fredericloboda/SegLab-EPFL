from __future__ import annotations
import os, sys, subprocess, time
from pathlib import Path
import lt_core as core

def now_ts() -> str:
    return time.strftime("%Y-%m-%d_%H%M%S")

def open_default(path: Path) -> None:
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        elif os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        pass

def open_smb_url() -> None:
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", core.SMB_URL])
        elif os.name == "nt":
            os.startfile(core.SMB_URL)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", core.SMB_URL])
    except Exception:
        pass

def guess_share_root() -> str:
    vol = Path("/Volumes")
    if vol.exists():
        for name in ["Hummel-Lab", "Hummel-Lab 1", "Hummel-Lab 2"]:
            p = vol / name
            if p.exists():
                if (p / "LTTrainer").exists():
                    return str((p / "LTTrainer").resolve())
                return str(p.resolve())
        for p in vol.iterdir():
            if p.is_dir() and "hummel" in p.name.lower():
                if (p / "LTTrainer").exists():
                    return str((p / "LTTrainer").resolve())
                return str(p.resolve())
    return ""

def is_nifti(p: Path) -> bool:
    n = p.name.lower()
    return n.endswith(".nii") or n.endswith(".nii.gz")

def norm_code(s: str) -> str:
    s = (s or "").strip().upper()
    return "".join([c for c in s if c.isalnum() or c in ("-", "_")])
