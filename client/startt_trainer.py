#!/usr/bin/env python3
# startt_trainer.py — modular LT Trainer client (offline + SMB classroom)

from __future__ import annotations
import os, sys
from pathlib import Path
from typing import Dict, Any, Optional

if sys.platform == "darwin":
    os.environ.setdefault("QT_MAC_WANTS_LAYER", "1")
    os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QStackedWidget, QMessageBox
)

import lt_core as core
import lt_style as style
import lt_share as share

from ui.widgets import pill, btn
from ui.pages_gate import GatePage
from ui.pages_dashboard import DashboardPage
from ui.pages_connect import ConnectPage
from ui.pages_materials import MaterialsPage
from ui.pages_practice import PracticePage
from ui.pages_progress import ProgressPage
from ui.pages_teacher import TeacherPage
from ui.pages_teacher_dash import TeacherDashboardPage
from ui.pages_settings import SettingsPage

NAV = ["Gate","Dashboard","Connect","Materials","Practice","Progress","Teacher","Teacher Dashboard","Settings"]

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        core.ensure_dirs()

        self.setWindowTitle(f"{core.APP_NAME} — v{core.APP_VERSION}")
        self.resize(1440, 840)

        self.mode: str = "gate"   # gate|solo|student|teacher
        self.username: str = str(core.cfg_get("username","student") or "student")
        self.share_root: Optional[Path] = None
        self.class_code: str = str(core.cfg_get("class_code","") or "")
        self.locked_policy: Optional[Dict[str,Any]] = None

        self.solo_min_voxels = int(core.cfg_get("solo_min_voxels", core.DEFAULT_MIN_VOXELS))
        self.solo_tolerance = int(core.cfg_get("solo_tolerance", core.DEFAULT_TOLERANCE))

        root = QWidget(); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(14,14,14,14); outer.setSpacing(12)

        self.top = QWidget(); self.top.setObjectName("TopBar")
        tb = QHBoxLayout(self.top); tb.setContentsMargins(16,10,16,10); tb.setSpacing(12)
        self.lbl_title = QLabel(core.APP_NAME); self.lbl_title.setObjectName("AppTitle")
        tb.addWidget(self.lbl_title); tb.addStretch(1)

        self.p_mode = pill("GATE")
        self.p_class = pill("NO CLASS")
        self.p_user = pill("USER")
        tb.addWidget(self.p_mode); tb.addWidget(self.p_class); tb.addWidget(self.p_user)

        self.b_gate = btn("Gate","ghost")
        self.b_solo = btn("Solo","ghost")
        tb.addWidget(self.b_gate); tb.addWidget(self.b_solo)
        self.b_gate.clicked.connect(lambda: self.goto("Gate"))
        self.b_solo.clicked.connect(self.enter_solo)

        outer.addWidget(self.top)

        main = QHBoxLayout(); main.setSpacing(12)
        outer.addLayout(main, 1)

        self.sidebar = QWidget(); self.sidebar.setObjectName("Sidebar")
        sb = QVBoxLayout(self.sidebar); sb.setContentsMargins(10,10,10,10); sb.setSpacing(10)

        self.nav = QListWidget()
        for name in NAV:
            self.nav.addItem(QListWidgetItem(name))
        self.nav.currentRowChanged.connect(self._on_nav)
        sb.addWidget(self.nav, 1)
        main.addWidget(self.sidebar, 0)

        self.stack = QStackedWidget()
        main.addWidget(self.stack, 1)

        self.pages = {
            "Gate": GatePage(self),
            "Dashboard": DashboardPage(self),
            "Connect": ConnectPage(self),
            "Materials": MaterialsPage(self),
            "Practice": PracticePage(self),
            "Progress": ProgressPage(self),
            "Teacher": TeacherPage(self),
            "Teacher Dashboard": TeacherDashboardPage(self),
            "Settings": SettingsPage(self),
        }
        for name in NAV:
            self.stack.addWidget(self.pages[name])

        app = QApplication.instance()
        if app is not None:
            style.apply_qss(app)

        self.goto("Gate")
        self.refresh_all()

    def toast(self, msg: str):
        try:
            self.statusBar().showMessage(str(msg or ""), 4500)
        except Exception:
            pass

    def quit_for_update(self):
        try:
            self.close()
        except Exception:
            pass
        try:
            QApplication.instance().quit()
        except Exception:
            pass

    def attempts_dir(self) -> Path:
        uname = self.username or "student"
        if self.mode == "student" and self.share_root and self.class_code:
            return share.attempts_root(self.share_root, self.class_code) / uname
        return core.LOCAL_PROGRESS / uname

    def _update_nav_visibility(self):
        if self.mode == "gate":
            visible = {"Gate","Dashboard","Materials","Connect","Teacher"}
        elif self.mode == "solo":
            visible = {"Gate","Dashboard","Materials","Practice","Progress","Settings","Connect","Teacher"}
        elif self.mode == "student":
            visible = {"Gate","Dashboard","Materials","Practice","Progress","Connect"}
        elif self.mode == "teacher":
            visible = {"Gate","Dashboard","Materials","Teacher","Teacher Dashboard","Practice","Progress","Settings"}
        else:
            visible = set(NAV)

        for i in range(self.nav.count()):
            it = self.nav.item(i)
            if it:
                it.setHidden(it.text() not in visible)

    def refresh_all(self):
        self.p_mode.setText(self.mode.upper())
        self.p_user.setText((self.username or "USER").upper())
        self.p_class.setText(self.class_code if self.class_code else "NO CLASS")
        self._update_nav_visibility()

        try:
            name = NAV[self.stack.currentIndex()]
            p = self.pages.get(name)
            if p and hasattr(p, "refresh"):
                p.refresh()
        except Exception:
            pass

    def goto(self, name: str):
        if name not in NAV:
            return
        self.nav.setCurrentRow(NAV.index(name))

    def _on_nav(self, idx: int):
        if idx < 0:
            return
        it = self.nav.item(idx)
        if not it:
            return
        name = it.text()
        if name not in NAV:
            return
        self.stack.setCurrentIndex(NAV.index(name))
        p = self.pages.get(name)
        if p and hasattr(p, "refresh"):
            try:
                p.refresh()
            except Exception:
                pass

    def enter_solo(self):
        self.mode = "solo"
        self.class_code = ""
        self.locked_policy = None
        core.cfg_set("username", self.username)
        self.refresh_all()
        self.goto("Dashboard")

    def enter_teacher(self, share_root: Path):
        self.mode = "teacher"
        self.share_root = share_root
        core.cfg_set("share_root", str(share_root))
        cc = str(core.cfg_get("class_code","") or "")
        if cc and share.class_exists(share_root, cc):
            self.class_code = cc
            self.locked_policy = share.policy_load(share_root, cc)
        else:
            self.class_code = ""
            self.locked_policy = None
        self.refresh_all()
        self.goto("Dashboard")

    def join_classroom(self, share_path: str, class_code: str, username: str):
        p = Path(share_path).expanduser()
        if not p.exists():
            QMessageBox.critical(self, core.APP_NAME, f"Mounted share path does not exist:\n{p}")
            return

        root = share.resolve_share_root(p)
        code = class_code
        share.ensure_classroom(root, code)

        self.share_root = root
        self.username = (username or "student").strip() or "student"
        self.mode = "student"
        self.class_code = code
        core.cfg_set("username", self.username)
        core.cfg_set("share_root", str(root))
        core.cfg_set("class_code", code)

        self.locked_policy = share.policy_load(root, code) or {
            "min_voxels": core.DEFAULT_MIN_VOXELS,
            "tolerance": core.DEFAULT_TOLERANCE,
            "session": "practice",
        }

        self.refresh_all()
        self.goto("Dashboard")
        QMessageBox.information(self, core.APP_NAME, f"Joined classroom: {code}\n\nNow go to Practice → Sync classroom cases.")

def main():
    app = QApplication(sys.argv)
    w = AppWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
