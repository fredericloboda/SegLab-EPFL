from __future__ import annotations
import uuid
from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFileDialog, QMessageBox, QInputDialog
import lt_core as core
import lt_share as share
from lt_utils import open_smb_url, guess_share_root, norm_code, now_ts
from lt_eval import validate_pair
from ui.widgets import btn, h1, muted

class TeacherPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        v = QVBoxLayout(self)
        v.setContentsMargins(44, 34, 44, 34)
        v.setSpacing(12)

        v.addWidget(h1("Teacher"))
        v.addWidget(muted("""Teacher functions are protected by a PIN stored on the share.
After login: create classroom code, set policy, upload cases, view cohort dashboard."""))

        self.ed_share = QLineEdit()
        self.ed_share.setPlaceholderText("Mounted share path (e.g. /Volumes/Hummel-Lab or /Volumes/Hummel-Lab/LTTrainer)")
        self.ed_share.setText(str(core.cfg_get("share_root","") or ""))

        tools = QHBoxLayout()
        tools.setSpacing(10)
        self.b_mount = btn("Mount share…","ghost")
        self.b_detect = btn("Auto-detect","ghost")
        self.b_browse = btn("Browse…","ghost")
        tools.addWidget(self.b_mount)
        tools.addWidget(self.b_detect)
        tools.addWidget(self.b_browse)
        tools.addStretch(1)

        v.addWidget(QLabel("Mounted share path"))
        v.addWidget(self.ed_share)
        v.addLayout(tools)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.b_setpin = btn("Set / change PIN","ghost")
        self.b_login = btn("Teacher login","primary")
        row.addWidget(self.b_setpin)
        row.addWidget(self.b_login)
        row.addStretch(1)
        v.addLayout(row)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.b_create = btn("Create classroom","ghost")
        self.b_policy = btn("Set policy","ghost")
        self.b_upload = btn("Upload case","ghost")
        self.b_dash = btn("Open teacher dashboard","primary")
        row2.addWidget(self.b_create)
        row2.addWidget(self.b_policy)
        row2.addWidget(self.b_upload)
        row2.addWidget(self.b_dash)
        row2.addStretch(1)
        v.addLayout(row2)

        self.info = muted("")
        v.addWidget(self.info)
        v.addStretch(1)

        self.b_mount.clicked.connect(open_smb_url)
        self.b_detect.clicked.connect(lambda: self.ed_share.setText(guess_share_root() or self.ed_share.text()))
        self.b_browse.clicked.connect(self._browse)
        self.b_setpin.clicked.connect(self._set_pin)
        self.b_login.clicked.connect(self._login)
        self.b_create.clicked.connect(self._create_class)
        self.b_policy.clicked.connect(self._policy)
        self.b_upload.clicked.connect(self._upload_case)
        self.b_dash.clicked.connect(lambda: self.app.goto("Teacher Dashboard"))

        self.refresh()

    def _browse(self):
        start = Path("/Volumes") if Path("/Volumes").exists() else Path.home()
        p = QFileDialog.getExistingDirectory(self, "Select mounted share folder", str(start))
        if p:
            self.ed_share.setText(p)

    def _root(self) -> Path | None:
        sp = self.ed_share.text().strip()
        if not sp:
            QMessageBox.critical(self, core.APP_NAME, "Share path is empty.")
            return None
        p = Path(sp).expanduser()
        if not p.exists():
            QMessageBox.critical(self, core.APP_NAME, f"Share path does not exist:\n{p}\n\nMount SMB share first.")
            return None
        root = share.resolve_share_root(p)
        core.cfg_set("share_root", str(root))
        return root

    def _set_pin(self):
        root = self._root()
        if not root:
            return
        pin, ok = QInputDialog.getText(self, "Teacher PIN", "Set a Teacher PIN (min 4 chars):", QLineEdit.Password)
        if not ok:
            return
        pin = (pin or "").strip()
        if len(pin) < 4:
            QMessageBox.critical(self, core.APP_NAME, "PIN too short.")
            return
        share.pin_set(root, pin)
        QMessageBox.information(self, core.APP_NAME, "PIN saved on share.")
        self.refresh()

    def _login(self):
        root = self._root()
        if not root:
            return
        if not share.pin_is_set(root):
            QMessageBox.information(self, core.APP_NAME, "No PIN found on share. Set one first.")
            return
        pin, ok = QInputDialog.getText(self, "Teacher login", "Enter Teacher PIN:", QLineEdit.Password)
        if not ok:
            return
        if not share.pin_verify(root, (pin or "").strip()):
            QMessageBox.critical(self, core.APP_NAME, "Wrong PIN.")
            return
        self.app.enter_teacher(root)
        QMessageBox.information(self, core.APP_NAME, "Teacher authenticated.")
        self.refresh()

    def _create_class(self):
        if self.app.mode != "teacher" or not self.app.share_root:
            QMessageBox.information(self, core.APP_NAME, "Login as teacher first.")
            return
        code, ok = QInputDialog.getText(self, "Create classroom", "Classroom code (e.g. HUMMEL2026):")
        if not ok:
            return
        code = norm_code(code)
        if not code:
            QMessageBox.critical(self, core.APP_NAME, "Invalid code.")
            return
        share.ensure_classroom(self.app.share_root, code)
        self.app.class_code = code
        core.cfg_set("class_code", code)
        self.app.locked_policy = share.policy_load(self.app.share_root, code)
        QMessageBox.information(self, core.APP_NAME, f"Classroom ready: {code}")
        self.app.refresh_all()

    def _policy(self):
        if self.app.mode != "teacher" or not self.app.share_root or not self.app.class_code:
            QMessageBox.information(self, core.APP_NAME, "Teacher must be logged in and have a classroom selected.")
            return
        pol = share.policy_load(self.app.share_root, self.app.class_code)
        mv = int(pol.get("min_voxels", core.DEFAULT_MIN_VOXELS))
        tol = int(pol.get("tolerance", core.DEFAULT_TOLERANCE))
        mv2, ok = QInputDialog.getInt(self, "Policy", "Minimum lesion voxels:", mv, 1, 100000, 1)
        if not ok:
            return
        tol2, ok = QInputDialog.getInt(self, "Policy", "Tolerance (mismatch voxels):", tol, 0, 10000000, 10)
        if not ok:
            return
        pol["min_voxels"] = int(mv2)
        pol["tolerance"] = int(tol2)
        share.policy_save(self.app.share_root, self.app.class_code, pol)
        self.app.locked_policy = pol
        QMessageBox.information(self, core.APP_NAME, "Policy saved.")
        self.app.refresh_all()

    def _upload_case(self):
        if self.app.mode != "teacher" or not self.app.share_root or not self.app.class_code:
            QMessageBox.information(self, core.APP_NAME, "Login as teacher and create/select a classroom first.")
            return
        t1_fp, _ = QFileDialog.getOpenFileName(self, "Select T1 (NIfTI)", str(Path.home()), "NIfTI (*.nii *.nii.gz)")
        if not t1_fp:
            return
        gold_fp, _ = QFileDialog.getOpenFileName(self, "Select gold mask (NIfTI)", str(Path.home()), "NIfTI (*.nii *.nii.gz)")
        if not gold_fp:
            return
        t1 = Path(t1_fp)
        gold = Path(gold_fp)
        ok, msg, meta = validate_pair(t1, gold)
        if not ok:
            QMessageBox.critical(self, core.APP_NAME, msg)
            return
        case_id = f"case_{now_ts()}_{uuid.uuid4().hex[:6]}"
        dest = share.upload_case(self.app.share_root, self.app.class_code, case_id, t1, gold)
        try:
            import os
            os.chmod(dest / "gold.nii.gz", 0o444)
        except Exception:
            pass
        (dest / "case.json").write_text(str({"case_id": case_id, **meta}), encoding="utf-8")
        QMessageBox.information(self, core.APP_NAME, f"Uploaded: {case_id}")
        self.app.refresh_all()

    def refresh(self):
        if self.app.mode == "teacher" and self.app.share_root:
            self.info.setText(f"Authenticated TEACHER\nShare root: {self.app.share_root}\nClassroom: {self.app.class_code or '—'}")
        else:
            self.info.setText("Not authenticated.")
