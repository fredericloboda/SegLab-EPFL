from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFileDialog, QMessageBox
import lt_core as core
from lt_utils import open_smb_url, guess_share_root, norm_code
from ui.widgets import btn, h1, muted

class ConnectPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        v = QVBoxLayout(self)
        v.setContentsMargins(44, 34, 44, 34)
        v.setSpacing(12)

        v.addWidget(h1("Connect / Join classroom"))
        v.addWidget(muted(r"""This uses the mounted SMB folder path (NOT smb://...).
Mount first, then select the mounted folder.
macOS: /Volumes/Hummel-Lab/...   Windows: X:\\...
"""))

        self.ed_share = QLineEdit()
        self.ed_share.setPlaceholderText("Mounted folder path (e.g. /Volumes/Hummel-Lab/LTTrainer)")
        self.ed_share.setText(str(core.cfg_get("share_root", "") or ""))

        tools = QHBoxLayout()
        tools.setSpacing(10)
        b_mount = btn("Mount share…", "ghost")
        b_detect = btn("Auto-detect", "ghost")
        b_browse = btn("Browse…", "ghost")
        tools.addWidget(b_mount)
        tools.addWidget(b_detect)
        tools.addWidget(b_browse)
        tools.addStretch(1)

        self.ed_code = QLineEdit()
        self.ed_code.setPlaceholderText("Classroom code (teacher provides it)")
        self.ed_code.setText(str(core.cfg_get("class_code", "") or ""))

        self.ed_name = QLineEdit()
        self.ed_name.setPlaceholderText("Your name")
        self.ed_name.setText(str(core.cfg_get("username", "student") or "student"))

        v.addWidget(QLabel("Mounted share path"))
        v.addWidget(self.ed_share)
        v.addLayout(tools)

        v.addWidget(QLabel("Classroom code"))
        v.addWidget(self.ed_code)

        v.addWidget(QLabel("Your name"))
        v.addWidget(self.ed_name)

        act = QHBoxLayout()
        act.setSpacing(12)
        self.b_join = btn("Join classroom (Student)", "primary")
        self.b_offline = btn("Continue offline (Solo)", "ghost")
        act.addWidget(self.b_join)
        act.addWidget(self.b_offline)
        act.addStretch(1)
        v.addLayout(act)
        v.addStretch(1)

        b_mount.clicked.connect(open_smb_url)
        b_detect.clicked.connect(lambda: self.ed_share.setText(guess_share_root() or self.ed_share.text()))
        b_browse.clicked.connect(self._browse)
        self.b_offline.clicked.connect(self.app.enter_solo)
        self.b_join.clicked.connect(self._join)

    def _browse(self):
        start = Path("/Volumes") if Path("/Volumes").exists() else Path.home()
        p = QFileDialog.getExistingDirectory(self, "Select mounted share folder", str(start))
        if p:
            self.ed_share.setText(p)

    def _join(self):
        sp = self.ed_share.text().strip()
        code = norm_code(self.ed_code.text().strip())
        uname = (self.ed_name.text().strip() or "student")
        if not sp:
            QMessageBox.critical(self, core.APP_NAME, "Share path is empty.")
            return
        if not code:
            QMessageBox.critical(self, core.APP_NAME, "Classroom code is empty/invalid.")
            return
        self.app.join_classroom(sp, code, uname)

    def refresh(self):
        pass
