from __future__ import annotations

import csv
import json
import os
import platform
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

import lt_core as core
import lt_utils as u


def validate_pair(t1: Path, gold: Path) -> Tuple[bool, str, Dict[str, Any]]:
    if not u.is_nifti(t1) or not u.is_nifti(gold):
        return False, "Select NIfTI files (.nii / .nii.gz).", {}
    meta: Dict[str, Any] = {}
    try:
        import nibabel as nib

        t1i = nib.load(str(t1))
        gi = nib.load(str(gold))
        meta["t1_shape"] = list(t1i.shape)
        meta["gold_shape"] = list(gi.shape)
        if t1i.shape[:3] != gi.shape[:3]:
            return False, f"Shape mismatch: T1 {t1i.shape} vs GOLD {gi.shape}", meta
        return True, "OK", meta
    except Exception:
        return True, "OK (limited validation)", meta


def make_blank_student_mask(ref_t1: Path, out_mask: Path) -> Tuple[bool, str]:
    try:
        import numpy as np
        import nibabel as nib

        img = nib.load(str(ref_t1))
        data = np.zeros(img.shape[:3], dtype=np.uint8)
        out = nib.Nifti1Image(data, img.affine, img.header)
        nib.save(out, str(out_mask))
        return True, "OK"
    except Exception as e:
        return False, f"Could not create blank mask: {e}"


def evaluate_masks(gold: Path, student: Path) -> Tuple[bool, str, Dict[str, Any]]:
    """Study-friendly binary mask evaluation.

    Returned metrics are deliberately *analysis-ready* (CSV/JSONL) for later papers.
    """
    try:
        import numpy as np
        import nibabel as nib

        gi = nib.load(str(gold))
        si = nib.load(str(student))

        g = gi.get_fdata()
        s = si.get_fdata()
        gb = (g > 0.5)
        sb = (s > 0.5)

        tp = int((gb & sb).sum())
        fp = int((~gb & sb).sum())
        fn = int((gb & ~sb).sum())
        total = int(gb.size)
        tn = int(total - tp - fp - fn)

        gvox = int(gb.sum())
        svox = int(sb.sum())

        denom_dice = (2 * tp + fp + fn)
        dice = (2.0 * tp / denom_dice) if denom_dice > 0 else 1.0

        denom_j = (tp + fp + fn)
        jaccard = (float(tp) / denom_j) if denom_j > 0 else 1.0

        precision = (float(tp) / (tp + fp)) if (tp + fp) > 0 else (1.0 if gvox == 0 else 0.0)
        recall = (float(tp) / (tp + fn)) if (tp + fn) > 0 else 1.0
        specificity = (float(tn) / (tn + fp)) if (tn + fp) > 0 else 1.0
        accuracy = (float(tp + tn) / total) if total > 0 else 1.0

        mismatch = int((gb ^ sb).sum())

        # voxel volume (mm^3) and lesion volumes (ml)
        try:
            zooms = gi.header.get_zooms()[:3]
            vox_mm3 = float(zooms[0] * zooms[1] * zooms[2])
        except Exception:
            vox_mm3 = 1.0
        gold_ml = float(gvox * vox_mm3 / 1000.0)
        student_ml = float(svox * vox_mm3 / 1000.0)
        vol_abs_err_ml = float(abs(student_ml - gold_ml))
        vol_rel_err = float((student_ml - gold_ml) / gold_ml) if gold_ml > 0 else (0.0 if student_ml == 0 else 1.0)

        # centroid distance (mm)
        def _centroid_mm(mask: "np.ndarray", affine) -> Optional[Tuple[float, float, float]]:
            if int(mask.sum()) == 0:
                return None
            pts = np.argwhere(mask)
            c_vox = pts.mean(axis=0)
            c_mm = nib.affines.apply_affine(affine, c_vox)
            return float(c_mm[0]), float(c_mm[1]), float(c_mm[2])

        c_g = _centroid_mm(gb, gi.affine)
        c_s = _centroid_mm(sb, gi.affine)
        centroid_dist_mm = None
        if c_g and c_s:
            dx = c_g[0] - c_s[0]
            dy = c_g[1] - c_s[1]
            dz = c_g[2] - c_s[2]
            centroid_dist_mm = float((dx * dx + dy * dy + dz * dz) ** 0.5)

        return True, "OK", {
            "dice": float(dice),
            "jaccard": float(jaccard),
            "precision": float(precision),
            "recall": float(recall),
            "specificity": float(specificity),
            "accuracy": float(accuracy),
            "tp": int(tp),
            "fp": int(fp),
            "fn": int(fn),
            "tn": int(tn),
            "gold_voxels": int(gvox),
            "student_voxels": int(svox),
            "mismatch_voxels": int(mismatch),
            "vox_mm3": float(vox_mm3),
            "gold_ml": float(gold_ml),
            "student_ml": float(student_ml),
            "vol_abs_err_ml": float(vol_abs_err_ml),
            "vol_rel_err": float(vol_rel_err),
            "centroid_dist_mm": centroid_dist_mm,
        }
    except Exception as e:
        return False, f"Evaluation requires nibabel+numpy. {e}", {}


ATTEMPT_FIELDS = [
    "timestamp",
    "app_version",
    "platform",
    "user",
    "mode",
    "class_code",
    "case_id",
    "session",
    "min_voxels",
    "tolerance",
    "passed",
    "dice",
    "jaccard",
    "precision",
    "recall",
    "specificity",
    "accuracy",
    "mismatch_voxels",
    "gold_voxels",
    "student_voxels",
    "tp",
    "fp",
    "fn",
    "tn",
    "vox_mm3",
    "gold_ml",
    "student_ml",
    "vol_abs_err_ml",
    "vol_rel_err",
    "centroid_dist_mm",
    "editor",
]


def write_attempt(out_dir: Path, attempt: Dict[str, Any]) -> None:
    """Write one attempt in 3 forms: JSON, JSONL, CSV."""
    out_dir.mkdir(parents=True, exist_ok=True)

    attempt.setdefault("app_version", getattr(core, "APP_VERSION", ""))
    attempt.setdefault("platform", platform.platform())

    ts = str(attempt.get("timestamp") or "")
    rid = str(attempt.get("_rid") or os.urandom(3).hex())

    # 1) individual JSON (human readable)
    try:
        (out_dir / f"{ts}_{rid}.json").write_text(json.dumps(attempt, indent=2), encoding="utf-8")
    except Exception:
        pass

    # 2) JSONL (analysis-friendly)
    try:
        with (out_dir / "attempts.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(attempt, ensure_ascii=False) + "\n")
    except Exception:
        pass

    # 3) CSV (analysis-friendly)
    csv_path = out_dir / "attempts.csv"
    row = {k: attempt.get(k, "") for k in ATTEMPT_FIELDS}
    try:
        write_header = not csv_path.exists()
        with csv_path.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=ATTEMPT_FIELDS)
            if write_header:
                w.writeheader()
            w.writerow(row)
    except Exception:
        pass
