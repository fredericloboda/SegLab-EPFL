from __future__ import annotations
import json
from typing import Any, Dict, List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
import lt_share as share
from ui.widgets import btn, h1, muted
from lt_utils import open_default

class TeacherDashboardPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        v = QVBoxLayout(self)
        v.setContentsMargins(44, 34, 44, 34)
        v.setSpacing(12)

        v.addWidget(h1("Teacher Dashboard"))
        v.addWidget(muted("Cohort leaderboard + per-case difficulty from attempts written to the share."))

        self.tbl_leader = QTableWidget(0,4)
        self.tbl_leader.setHorizontalHeaderLabels(["Student","Attempts","Avg Dice","Pass rate"])
        self.tbl_leader.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_leader.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tbl_cases = QTableWidget(0,4)
        self.tbl_cases.setHorizontalHeaderLabels(["Case","Attempts","Avg Dice","Avg mismatch"])
        self.tbl_cases.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_cases.setEditTriggers(QAbstractItemView.NoEditTriggers)

        v.addWidget(QLabel("Leaderboard"))
        v.addWidget(self.tbl_leader, 1)
        v.addWidget(QLabel("Case difficulty"))
        v.addWidget(self.tbl_cases, 1)

        row = QHBoxLayout(); row.setSpacing(10)
        self.b_refresh = btn("Refresh","primary")
        self.b_open = btn("Open attempts on share","ghost")
        row.addWidget(self.b_refresh); row.addWidget(self.b_open); row.addStretch(1)
        v.addLayout(row)

        self.b_refresh.clicked.connect(self.refresh)
        self.b_open.clicked.connect(self._open_attempts)

    def _attempts_root(self):
        if not self.app.share_root or not self.app.class_code:
            return None
        return share.attempts_root(self.app.share_root, self.app.class_code)

    def _open_attempts(self):
        p = self._attempts_root()
        if p and p.exists():
            open_default(p)

    def refresh(self):
        self.tbl_leader.setRowCount(0)
        self.tbl_cases.setRowCount(0)

        if self.app.mode != "teacher" or not self.app.share_root or not self.app.class_code:
            return

        root = self._attempts_root()
        if not root or not root.exists():
            return

        attempts: List[Dict[str,Any]] = []
        for user_dir in [p for p in root.iterdir() if p.is_dir()]:
            for f in user_dir.glob("*.json"):
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(d, dict):
                        attempts.append(d)
                except Exception:
                    pass

        if not attempts:
            return

        by_user: Dict[str, List[Dict[str,Any]]] = {}
        for a in attempts:
            u = str(a.get("user") or "unknown")
            by_user.setdefault(u, []).append(a)

        leader = []
        for u, arr in by_user.items():
            n = len(arr)
            avg_d = sum(float(x.get("dice") or 0.0) for x in arr) / max(1, n)
            pr = sum(1 for x in arr if x.get("passed")) / max(1, n)
            leader.append((u, n, avg_d, pr))
        leader.sort(key=lambda x: (x[2], x[1]), reverse=True)

        for u, n, avg_d, pr in leader:
            r = self.tbl_leader.rowCount(); self.tbl_leader.insertRow(r)
            self.tbl_leader.setItem(r,0,QTableWidgetItem(u))
            self.tbl_leader.setItem(r,1,QTableWidgetItem(str(n)))
            self.tbl_leader.setItem(r,2,QTableWidgetItem(f"{avg_d:.3f}"))
            self.tbl_leader.setItem(r,3,QTableWidgetItem(f"{pr*100:.1f}%"))

        by_case: Dict[str, List[Dict[str,Any]]] = {}
        for a in attempts:
            c = str(a.get("case_id") or "")
            if c:
                by_case.setdefault(c, []).append(a)

        cases = []
        for c, arr in by_case.items():
            n = len(arr)
            avg_d = sum(float(x.get("dice") or 0.0) for x in arr) / max(1, n)
            avg_m = sum(float(x.get("mismatch_voxels") or 0.0) for x in arr) / max(1, n)
            cases.append((c, n, avg_d, avg_m))
        cases.sort(key=lambda x: (x[2], -x[1]))

        for c, n, avg_d, avg_m in cases:
            r = self.tbl_cases.rowCount(); self.tbl_cases.insertRow(r)
            self.tbl_cases.setItem(r,0,QTableWidgetItem(c))
            self.tbl_cases.setItem(r,1,QTableWidgetItem(str(n)))
            self.tbl_cases.setItem(r,2,QTableWidgetItem(f"{avg_d:.3f}"))
            self.tbl_cases.setItem(r,3,QTableWidgetItem(f"{avg_m:.0f}"))
