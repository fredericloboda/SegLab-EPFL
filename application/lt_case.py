from __future__ import annotations
import json, os, shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import lt_core as core

@dataclass
class CaseRow:
    case_id: str
    source: str
    case_dir: Path
    t1: Path
    gold: Path
    student: Path
    meta: Dict[str, Any]

def set_readonly(p: Path) -> None:
    try:
        if p.exists():
            os.chmod(p, 0o444)
    except Exception:
        pass

def write_case(case_dir: Path, case_id: str, extra: Dict[str, Any]) -> None:
    meta = {"case_id": case_id, **(extra or {})}
    (case_dir / "case.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

def load_case(case_dir: Path) -> Optional[CaseRow]:
    try:
        mp = case_dir / "case.json"
        if not mp.exists():
            return None
        meta = json.loads(mp.read_text(encoding="utf-8"))
        cid = str(meta.get("case_id") or case_dir.name)
        t1 = case_dir / "t1.nii.gz"
        gold = case_dir / "gold.nii.gz"
        student = case_dir / "student.nii.gz"
        if not t1.exists() or not gold.exists():
            return None
        source = "WORK" if str(case_dir).startswith(str(core.WORKSPACE)) else "LOCAL"
        return CaseRow(cid, source, case_dir, t1, gold, student, meta if isinstance(meta, dict) else {})
    except Exception:
        return None

def list_cases() -> List[CaseRow]:
    out: List[CaseRow] = []
    for base in (core.WORKSPACE, core.LOCAL_CASES):
        if not base.exists():
            continue
        for d in sorted([p for p in base.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
            c = load_case(d)
            if c:
                out.append(c)
    return out
