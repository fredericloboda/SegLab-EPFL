from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox
)

import lt_core as core
from lt_utils import open_default
from ui.widgets import btn, h1, muted


def _safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)


class TinyLinePlot(QWidget):
    """
    Lightweight plot widget (no matplotlib).
    Shows values (0..1) over an index (attempt order).
    """
    def __init__(self, title: str = ""):
        super().__init__()
        self._title = title
        self._values: List[float] = []
        self.setMinimumHeight(180)

    def set_series(self, title: str, values: List[float]):
        self._title = str(title or "")
        self._values = [float(v) for v in (values or [])]
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        r = self.rect().adjusted(10, 10, -10, -10)

        # panel
        p.setPen(QPen(QColor(255, 255, 255, 18)))
        p.setBrush(QColor(255, 255, 255, 10))
        p.drawRoundedRect(r, 16, 16)

        # title
        title_h = 26
        title_rect = r.adjusted(14, 8, -14, -(r.height() - title_h - 8))
        plot = r.adjusted(14, 8 + title_h, -14, -14)

        p.setPen(QPen(QColor(235, 235, 235, 220)))
        p.setFont(QFont(p.font().family(), 12, QFont.DemiBold))
        p.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, self._title)

        if len(self._values) < 2:
            p.setPen(QPen(QColor(160, 160, 160, 170)))
            p.setFont(QFont(p.font().family(), 11))
            p.drawText(plot, Qt.AlignCenter, "No attempts yet")
            return

        vmin = min(self._values)
        vmax = max(self._values)
        if abs(vmax - vmin) < 1e-9:
            vmax = vmin + 1.0

        def xy(i: int, v: float) -> Tuple[float, float]:
            x = plot.left() + plot.width() * (i / max(1, len(self._values) - 1))
            y = plot.bottom() - plot.height() * ((v - vmin) / (vmax - vmin))
            return x, y

        # grid lines
        p.setPen(QPen(QColor(255, 255, 255, 10), 1))
        for k in range(1, 4):
            y = plot.top() + (plot.height() * k / 4.0)
            p.drawLine(plot.left(), int(y), plot.right(), int(y))

        # polyline
        p.setPen(QPen(QColor(226, 0, 26, 230), 2))  # EPFL red
        last = None
        for i, v in enumerate(self._values):
            x, y = xy(i, v)
            if last is not None:
                p.drawLine(int(last[0]), int(last[1]), int(x), int(y))
            last = (x, y)

        # points
        p.setPen(QPen(QColor(255, 255, 255, 180), 1))
        p.setBrush(QColor(255, 255, 255, 180))
        for i, v in enumerate(self._values):
            x, y = xy(i, v)
            p.drawEllipse(int(x) - 2, int(y) - 2, 4, 4)

        # min/max labels
        p.setPen(QPen(QColor(180, 180, 180, 170)))
        p.setFont(QFont(p.font().family(), 10))
        p.drawText(plot.adjusted(4, 2, -4, -2), Qt.AlignTop | Qt.AlignLeft, f"{vmax:.3f}")
        p.drawText(plot.adjusted(4, 2, -4, -2), Qt.AlignBottom | Qt.AlignLeft, f"{vmin:.3f}")


class ProgressPage(QWidget):
    """
    Shows:
      - overall progress (Dice over all attempts)
      - per-case progress (Dice vs attempt # for selected case)
      - list of attempts (click to open JSON)
    """
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._attempts: List[Dict[str, Any]] = []
        self._case_ids: List[str] = []

        v = QVBoxLayout(self)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(12)

        v.addWidget(h1("Progress"))

        self.lbl_path = QLabel("")
        self.lbl_path.setWordWrap(True)
        self.lbl_path.setStyleSheet(f"color: {core.MUTED};")
        v.addWidget(self.lbl_path)

        # plots
        plots = QHBoxLayout()
        plots.setSpacing(12)
        self.plot_overall = TinyLinePlot("Overall Dice (all attempts)")
        self.plot_case = TinyLinePlot("Case Dice (selected case)")
        plots.addWidget(self.plot_overall, 1)
        plots.addWidget(self.plot_case, 1)
        v.addLayout(plots)

        # bottom row
        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        v.addLayout(bottom)

        # cases list
        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(muted("Cases"))
        self.list_cases = QListWidget()
        self.list_cases.setMinimumWidth(260)
        self.list_cases.currentRowChanged.connect(self._on_case_selected)
        left.addWidget(self.list_cases, 1)

        btns = QHBoxLayout()
        self.btn_open_folder = btn("Open attempts folder")
        self.btn_refresh = btn("Refresh")
        btns.addWidget(self.btn_open_folder)
        btns.addWidget(self.btn_refresh)
        left.addLayout(btns)

        self.btn_open_folder.clicked.connect(self._open_attempts_folder)
        self.btn_refresh.clicked.connect(self.refresh)

        bottom.addLayout(left, 0)

        # attempts list
        right = QVBoxLayout()
        right.setSpacing(8)
        right.addWidget(muted("Attempts (latest first)"))
        self.list_attempts = QListWidget()
        self.list_attempts.itemDoubleClicked.connect(self._open_attempt_json)
        right.addWidget(self.list_attempts, 1)
        bottom.addLayout(right, 1)

    # ---- data ----
    def _attempts_dir(self) -> Path:
        try:
            return Path(self.app.attempts_dir())
        except Exception:
            # fallback: local only
            uname = getattr(self.app, "username", None) or "student"
            return core.LOCAL_PROGRESS / uname

    def _load_attempts(self) -> List[Dict[str, Any]]:
        d = self._attempts_dir()
        jsonl = d / "attempts.jsonl"
        out: List[Dict[str, Any]] = []
        if not jsonl.exists():
            return out
        try:
            for line in jsonl.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        out.append(obj)
                except Exception:
                    continue
        except Exception:
            return out

        # newest first (timestamp is lexicographic sortable with now_ts)
        out.sort(key=lambda a: str(a.get("timestamp") or ""), reverse=True)
        return out

    def _extract_case_id(self, a: Dict[str, Any]) -> str:
        for k in ("case_id", "case", "id"):
            v = a.get(k)
            if v:
                return str(v)
        # fallback: maybe embedded
        return "unknown"

    def _case_attempt_series(self, case_id: str) -> List[float]:
        # oldest -> newest for attempt index
        items = [a for a in self._attempts if self._extract_case_id(a) == case_id]
        items.sort(key=lambda a: str(a.get("timestamp") or ""))
        return [_safe_float(a.get("dice", 0.0)) for a in items]

    # ---- UI ----
    def refresh(self):
        d = self._attempts_dir()
        self.lbl_path.setText(f"Attempts folder:\n{d}")

        self._attempts = self._load_attempts()

        # overall series (oldest -> newest)
        overall_oldest = list(reversed(self._attempts))
        overall = [_safe_float(a.get("dice", 0.0)) for a in overall_oldest]
        self.plot_overall.set_series("Overall Dice (all attempts)", overall)

        # cases list
        case_ids = []
        seen = set()
        for a in self._attempts:
            cid = self._extract_case_id(a)
            if cid not in seen:
                seen.add(cid)
                case_ids.append(cid)
        case_ids.sort()
        self._case_ids = case_ids

        self.list_cases.blockSignals(True)
        self.list_cases.clear()
        for cid in case_ids:
            self.list_cases.addItem(QListWidgetItem(cid))
        self.list_cases.blockSignals(False)

        # attempts list
        self.list_attempts.clear()
        for a in self._attempts[:500]:
            cid = self._extract_case_id(a)
            ts = str(a.get("timestamp") or "")
            dice = _safe_float(a.get("dice", 0.0))
            mm = a.get("mismatch_vox", a.get("voxel_mismatch", ""))
            txt = f"{ts}  |  {cid}  |  Dice {dice:.3f}  |  Δvox {mm}"
            it = QListWidgetItem(txt)
            it.setData(Qt.UserRole, a)
            self.list_attempts.addItem(it)

        # select first case automatically
        if self._case_ids:
            self.list_cases.setCurrentRow(0)
        else:
            self.plot_case.set_series("Case Dice (selected case)", [])

    def _on_case_selected(self, idx: int):
        if idx < 0 or idx >= len(self._case_ids):
            self.plot_case.set_series("Case Dice (selected case)", [])
            return
        cid = self._case_ids[idx]
        series = self._case_attempt_series(cid)
        self.plot_case.set_series(f"Case Dice — {cid}", series)

    def _open_attempts_folder(self):
        d = self._attempts_dir()
        try:
            open_default(str(d))
        except Exception as e:
            QMessageBox.information(self, "Open folder", str(e))

    def _open_attempt_json(self, item: QListWidgetItem):
        a = item.data(Qt.UserRole)
        if not isinstance(a, dict):
            return
        # find best JSON file (ts + rid)
        ts = str(a.get("timestamp") or "")
        rid = str(a.get("_rid") or "")
        d = self._attempts_dir()
        # try exact match
        if ts and rid:
            cand = d / f"{ts}_{rid}.json"
            if cand.exists():
                open_default(str(cand))
                return
        # fallback: open folder
        open_default(str(d))
