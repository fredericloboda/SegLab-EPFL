from __future__ import annotations
import json, shutil, uuid, re
from pathlib import Path
from typing import Dict, Any, List, Optional
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFileDialog, QMessageBox
)

import lt_core as core
import lt_share as share
from lt_utils import now_ts, open_default
from lt_eval import validate_pair, make_blank_student_mask, evaluate_masks, write_attempt
from lt_editor import launch as launch_editor
from lt_case import list_cases, set_readonly, write_case, CaseRow
from ui.widgets import btn, h1, muted

class PracticePage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        v = QVBoxLayout(self)
        v.setContentsMargins(44, 34, 44, 34)
        v.setSpacing(12)

        v.addWidget(h1("Practice"))
        v.addWidget(muted("""Workflow:
1) Get cases (Solo: Add case; Student: Sync classroom cases)
2) Click 'Test case' → ITK-SNAP opens T1 + your student mask
3) Save segmentation → auto-evaluation + progress logging
"""))

        # --- Solo case import (separate T1 + GOLD selection) ---
        self._pending_t1: Optional[Path] = None
        self._pending_gold: Optional[Path] = None

        self.import_bar = QWidget()
        ib = QHBoxLayout(self.import_bar)
        ib.setContentsMargins(0, 0, 0, 0)
        ib.setSpacing(10)
        self.import_bar.setMinimumHeight(56)

        self.lbl_pending = muted("Solo import: pick T1 + gold mask, then save as a case.")
        self.lbl_pending.setMinimumWidth(420)
        ib.addWidget(self.lbl_pending, 1)

        self.btn_pick_t1 = btn("Upload T1","ghost")
        self.btn_pick_gold = btn("Upload gold mask","ghost")
        self.btn_save_pending = btn("Save new case","primary")
        self.btn_save_pending.setEnabled(False)
        self.btn_batch = btn("Batch import…","ghost")

        ib.addWidget(self.btn_pick_t1)
        ib.addWidget(self.btn_pick_gold)
        ib.addWidget(self.btn_save_pending)
        ib.addWidget(self.btn_batch)

        v.addWidget(self.import_bar)

        self.btn_pick_t1.clicked.connect(self._pick_pending_t1)
        self.btn_pick_gold.clicked.connect(self._pick_pending_gold)
        self.btn_save_pending.clicked.connect(self._save_pending_case)
        self.btn_batch.clicked.connect(self._batch_import)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Case","Src","T1","Gold","Student","Status","Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)
        self.table.setWordWrap(False)
        self.table.setShowGrid(False)
        v.addSpacing(6)
        v.addWidget(self.table, 1)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.b_sync = btn("Sync classroom cases","ghost")
        self.b_open = btn("Open case folder","ghost")
        row.addWidget(self.b_sync)
        row.addWidget(self.b_open)
        row.addStretch(1)
        v.addLayout(row)

        self.b_sync.clicked.connect(self._sync_cases)
        self.b_open.clicked.connect(self._open_case_folder)

        self._rows: List[CaseRow] = []
        self._last_mtime: Dict[str, float] = {}

        self._timer = QTimer(self)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self._auto_check_student_masks)
        self._timer.start()

        self.refresh()

    def _selected(self) -> Optional[CaseRow]:
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return None
        idx = sel[0].row()
        return self._rows[idx] if 0 <= idx < len(self._rows) else None

    def refresh(self):
        self._rows = list_cases()
        self.table.setRowCount(0)
        for c in self._rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r,0,QTableWidgetItem(c.case_id))
            self.table.setItem(r,1,QTableWidgetItem(c.source))
            self.table.setItem(r,2,QTableWidgetItem(str(c.t1)))
            self.table.setItem(r,3,QTableWidgetItem(str(c.gold)))
            self.table.setItem(r,4,QTableWidgetItem(str(c.student) if c.student.exists() else "—"))
            self.table.setItem(r,5,QTableWidgetItem("HAS STUDENT MASK" if c.student.exists() else "READY"))
            b = btn("Test case","ghost")
            b.setMinimumHeight(34)
            b.setFixedHeight(36)
            b.clicked.connect(lambda _=False, cid=c.case_id: self._test_case(cid))
            self.table.setCellWidget(r,6,b)
        self._update_pending_ui()

    def _open_case_folder(self):
        c = self._selected()
        if not c:
            return
        open_default(c.case_dir)

    def _update_pending_ui(self):
        # Students cannot add cases in classroom mode
        solo_ok = getattr(self.app, "mode", "solo") != "student"
        try:
            self.import_bar.setVisible(bool(solo_ok))
        except Exception:
            pass

        t1 = self._pending_t1
        gold = self._pending_gold
        if t1 is None and gold is None:
            self.lbl_pending.setText("Solo import: pick T1 + gold mask, then save as a case.")
        else:
            t1s = t1.name if t1 else "—"
            gs = gold.name if gold else "—"
            self.lbl_pending.setText(f"Selected: T1={t1s} · GOLD={gs}")

        self.btn_save_pending.setEnabled(bool(solo_ok and t1 and gold))

    def _pick_pending_t1(self):
        if getattr(self.app, "mode", "solo") == "student":
            QMessageBox.information(self, core.APP_NAME, "Students cannot add cases in classroom mode. Use Sync.")
            return
        fp, _ = QFileDialog.getOpenFileName(self, "Select T1 (NIfTI)", str(Path.home()), "NIfTI (*.nii *.nii.gz)")
        if not fp:
            return
        self._pending_t1 = Path(fp)
        self._update_pending_ui()

    def _pick_pending_gold(self):
        if getattr(self.app, "mode", "solo") == "student":
            QMessageBox.information(self, core.APP_NAME, "Students cannot add cases in classroom mode. Use Sync.")
            return
        fp, _ = QFileDialog.getOpenFileName(self, "Select gold mask (NIfTI)", str(Path.home()), "NIfTI (*.nii *.nii.gz)")
        if not fp:
            return
        self._pending_gold = Path(fp)
        self._update_pending_ui()

    def _save_pending_case(self):
        if getattr(self.app, "mode", "solo") == "student":
            QMessageBox.information(self, core.APP_NAME, "Students cannot add cases in classroom mode.")
            return
        if not self._pending_t1 or not self._pending_gold:
            return
        t1 = self._pending_t1
        gold = self._pending_gold

        ok, msg, meta = validate_pair(t1, gold)
        if not ok:
            QMessageBox.critical(self, core.APP_NAME, msg)
            return

        # Construct case id from filename stem (safer when importing many)
        stem = t1.name
        stem = stem.replace(".nii.gz", "").replace(".nii", "")
        stem = re.sub(r"(?i)[_\-]t1$", "", stem)
        stem = re.sub(r"[^A-Za-z0-9_\-]+", "_", stem).strip("_")
        case_id = f"{stem}_{now_ts()}_{uuid.uuid4().hex[:4]}" if stem else f"case_{now_ts()}_{uuid.uuid4().hex[:6]}"

        dest = core.LOCAL_CASES / case_id
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(t1, dest/"t1.nii.gz")
        shutil.copy2(gold, dest/"gold.nii.gz")
        set_readonly(dest/"gold.nii.gz")
        write_case(dest, case_id, {"origin":"local_upload", **meta})

        # Ensure student mask exists
        try:
            if not (dest/"student.nii.gz").exists():
                make_blank_student_mask(dest/"t1.nii.gz", dest/"student.nii.gz")
        except Exception:
            pass

        self._pending_t1 = None
        self._pending_gold = None
        self._update_pending_ui()

        QMessageBox.information(self, core.APP_NAME, f"Case saved: {case_id}")
        self.refresh()

    def _batch_import(self):
        if getattr(self.app, "mode", "solo") == "student":
            QMessageBox.information(self, core.APP_NAME, "Students cannot add cases in classroom mode.")
            return

        folder = QFileDialog.getExistingDirectory(self, "Select folder with T1 + gold masks", str(Path.home()))
        if not folder:
            return
        folder_p = Path(folder)

        # Pairing heuristic: expects <id>_t1 + <id>_gold (or _mask/_lesion/_seg)
        def norm_key(p: Path) -> str:
            n = p.name
            n = n.replace(".nii.gz", "").replace(".nii", "")
            n2 = re.sub(r"(?i)[_\-](t1|img|image)$", "", n)
            n2 = re.sub(r"(?i)[_\-](gold|mask|lesion|seg|label)$", "", n2)
            return n2

        nifti = [p for p in folder_p.iterdir() if p.is_file() and p.name.lower().endswith((".nii", ".nii.gz"))]
        if not nifti:
            QMessageBox.information(self, core.APP_NAME, "No NIfTI files found in that folder.")
            return

        t1s = {}
        golds = {}
        for p in nifti:
            low = p.name.lower()
            k = norm_key(p)
            if re.search(r"(?i)(t1|_t1|\-t1)", low):
                t1s[k] = p
            elif re.search(r"(?i)(gold|mask|lesion|seg|label)", low):
                golds[k] = p

        keys = sorted(set(t1s.keys()) & set(golds.keys()))
        if not keys:
            QMessageBox.information(
                self,
                core.APP_NAME,
                "No pairs found. Naming expected e.g. CASE01_t1.nii.gz + CASE01_gold.nii.gz (or _mask/_lesion/_seg).",
            )
            return

        imported = 0
        skipped = 0
        for k in keys:
            t1 = t1s[k]
            gold = golds[k]
            ok, msg, meta = validate_pair(t1, gold)
            if not ok:
                skipped += 1
                continue
            case_id = f"{k}_{now_ts()}_{uuid.uuid4().hex[:4]}"
            dest = core.LOCAL_CASES / case_id
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(t1, dest/"t1.nii.gz")
            shutil.copy2(gold, dest/"gold.nii.gz")
            set_readonly(dest/"gold.nii.gz")
            write_case(dest, case_id, {"origin":"batch_import", "pair_key": k, **meta})
            try:
                if not (dest/"student.nii.gz").exists():
                    make_blank_student_mask(dest/"t1.nii.gz", dest/"student.nii.gz")
            except Exception:
                pass
            imported += 1

        QMessageBox.information(self, core.APP_NAME, f"Imported {imported} case(s). Skipped {skipped} (invalid pairs).")
        self.refresh()

    def _sync_cases(self):
        if self.app.mode != "student" or not self.app.share_root or not self.app.class_code:
            QMessageBox.information(self, core.APP_NAME, "Join a classroom first (Connect).")
            return
        src_cases = share.class_dir(self.app.share_root, self.app.class_code) / "cases"
        if not src_cases.exists():
            QMessageBox.critical(self, core.APP_NAME, f"No cases folder:\n{src_cases}")
            return
        copied = 0
        for case_folder in sorted([p for p in src_cases.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
            dest = core.WORKSPACE / case_folder.name
            if dest.exists():
                continue
            try:
                shutil.copytree(case_folder, dest)
                set_readonly(dest/"gold.nii.gz")
                copied += 1
            except Exception:
                pass
        QMessageBox.information(self, core.APP_NAME, f"Synced. New cases copied: {copied}")
        self.refresh()

    def _test_case(self, case_id: str):
        c = next((x for x in self._rows if x.case_id == case_id), None)
        if not c:
            return
        if not c.student.exists():
            ok, msg = make_blank_student_mask(c.t1, c.student)
            if not ok:
                QMessageBox.critical(self, core.APP_NAME, msg)
                return
        launch_editor(c.t1, c.student)
        self.app.toast(f"Opened editor for {c.case_id}. Save to student.nii.gz.")

    def _auto_check_student_masks(self):
        for c in self._rows:
            if not c.student.exists():
                continue
            key = str(c.student)
            try:
                m = c.student.stat().st_mtime
            except Exception:
                continue
            last = self._last_mtime.get(key)
            if last is None:
                self._last_mtime[key] = m
                continue
            if m > last + 0.5:
                self._last_mtime[key] = m
                self._auto_eval(c)

    def _auto_eval(self, c: CaseRow):
        ok, msg, metrics = evaluate_masks(c.gold, c.student)
        if not ok:
            self.app.toast(msg)
            return

        if self.app.mode == "student":
            pol = self.app.locked_policy or {}
            min_vox = int(pol.get("min_voxels", core.DEFAULT_MIN_VOXELS))
            tol = int(pol.get("tolerance", core.DEFAULT_TOLERANCE))
        else:
            min_vox = int(self.app.solo_min_voxels)
            tol = int(self.app.solo_tolerance)

        svox = int(metrics.get("student_voxels", 0))
        mismatch = int(metrics.get("mismatch_voxels", 0))
        dice = float(metrics.get("dice", 0.0))
        passed = (svox >= min_vox) and (mismatch <= tol)

        attempt = {
            "timestamp": now_ts(),
            "case_id": c.case_id,
            "mode": self.app.mode,
            "class_code": self.app.class_code or "",
            "user": self.app.username or "student",
            "session": getattr(self.app, "session", "practice"),
            "min_voxels": min_vox,
            "tolerance": tol,
            "passed": bool(passed),
            "editor": getattr(self.app, "editor", "external"),
            "_rid": uuid.uuid4().hex[:6],
            **metrics,
        }

        write_attempt(self.app.attempts_dir(), attempt)

        self.app.toast(
            f"{c.case_id}: Dice {dice:.3f} | J {float(metrics.get('jaccard',0.0)):.3f} | Δvox {mismatch} | {'PASS' if passed else 'NO PASS'}"
        )
        self.refresh()
