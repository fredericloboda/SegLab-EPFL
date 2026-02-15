from __future__ import annotations
import json, uuid, hashlib, shutil
from pathlib import Path
from typing import Any, Dict, List
import lt_core as core
from lt_utils import norm_code

def resolve_share_root(selected_path: Path) -> Path:
    p = selected_path.expanduser().resolve()
    if p.name.lower() == "lttrainer":
        root = p
    elif (p / "LTTrainer").exists():
        root = (p / "LTTrainer").resolve()
    else:
        root = (p / "LTTrainer").resolve()
    root.mkdir(parents=True, exist_ok=True)
    ensure_layout(root)
    return root

def ensure_layout(root: Path) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "classrooms").mkdir(parents=True, exist_ok=True)
    (root / "updates").mkdir(parents=True, exist_ok=True)

def pin_path(root: Path) -> Path:
    return root / "config" / "teacher_pin.json"

def _pin_hash(pin: str, salt: str) -> str:
    return hashlib.sha256((salt + "|" + pin).encode("utf-8")).hexdigest()

def pin_is_set(root: Path) -> bool:
    return pin_path(root).exists()

def pin_set(root: Path, pin: str) -> None:
    salt = uuid.uuid4().hex
    obj = {"salt": salt, "hash": _pin_hash(pin, salt)}
    pin_path(root).write_text(json.dumps(obj, indent=2), encoding="utf-8")

def pin_verify(root: Path, pin: str) -> bool:
    try:
        obj = json.loads(pin_path(root).read_text(encoding="utf-8"))
        salt = str(obj.get("salt") or "")
        h = str(obj.get("hash") or "")
        return bool(salt and h and _pin_hash(pin, salt) == h)
    except Exception:
        return False

def class_dir(root: Path, code: str) -> Path:
    return root / "classrooms" / norm_code(code)

def class_exists(root: Path, code: str) -> bool:
    return class_dir(root, code).exists()

def ensure_classroom(root: Path, code: str) -> Path:
    code = norm_code(code)
    cd = class_dir(root, code)
    (cd / "cases").mkdir(parents=True, exist_ok=True)
    (cd / "progress" / "attempts").mkdir(parents=True, exist_ok=True)
    (cd / "materials_protected").mkdir(parents=True, exist_ok=True)
    pol = cd / "config.json"
    if not pol.exists():
        pol.write_text(json.dumps({"min_voxels": core.DEFAULT_MIN_VOXELS, "tolerance": core.DEFAULT_TOLERANCE, "session": "practice"}, indent=2), encoding="utf-8")
    return cd

def policy_load(root: Path, code: str) -> Dict[str, Any]:
    try:
        p = class_dir(root, code) / "config.json"
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}

def policy_save(root: Path, code: str, d: Dict[str, Any]) -> None:
    p = class_dir(root, code) / "config.json"
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")

def list_class_cases(root: Path, code: str) -> List[Path]:
    cd = class_dir(root, code) / "cases"
    if not cd.exists():
        return []
    return sorted([p for p in cd.iterdir() if p.is_dir()], key=lambda x: x.name.lower())

def upload_case(root: Path, code: str, case_id: str, t1: Path, gold: Path) -> Path:
    dest = class_dir(root, code) / "cases" / case_id
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(t1, dest / "t1.nii.gz")
    shutil.copy2(gold, dest / "gold.nii.gz")
    return dest

def attempts_root(root: Path, code: str) -> Path:
    return class_dir(root, code) / "progress" / "attempts"
