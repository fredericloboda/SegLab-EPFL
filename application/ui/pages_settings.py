from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QInputDialog, QMessageBox, QLabel
)

import lt_core as core
import lt_update as upd
from ui.widgets import btn, h1, muted, Card


class SettingsPage(QWidget):
    """Settings are ONLY meant for SOLO (offline) practice.
    In classroom mode, policy is locked by teacher and shown read-only.
    """

    def __init__(self, app):
        super().__init__()
        self.app = app

        v = QVBoxLayout(self)
        v.setContentsMargins(44, 34, 44, 34)
        v.setSpacing(14)

        v.addWidget(h1("Settings"))

        self.info = QLabel()
        self.info.setWordWrap(True)
        v.addWidget(self.info)

        card = Card()
        v.addWidget(card)
        grid = QGridLayout(card)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.addWidget(muted("Min lesion voxels (solo practice)"), 0, 0)
        self.b_minvox = btn("Set", "ghost")
        grid.addWidget(self.b_minvox, 0, 1)

        grid.addWidget(muted("Voxel mismatch tolerance (solo practice)"), 1, 0)
        self.b_tol = btn("Set", "ghost")
        grid.addWidget(self.b_tol, 1, 1)

        grid.addWidget(muted("Update feed URL (latest.json)"), 2, 0)
        self.b_update_url = btn("Set", "ghost")
        grid.addWidget(self.b_update_url, 2, 1)

        self.b_check = btn("Check for updates", "primary")
        grid.addWidget(self.b_check, 3, 0, 1, 2)

        self.b_minvox.clicked.connect(self._set_minvox)
        self.b_tol.clicked.connect(self._set_tol)
        self.b_update_url.clicked.connect(self._set_update_url)
        self.b_check.clicked.connect(self._check_updates)

        v.addStretch(1)
        self.refresh()

    def refresh(self):
        locked = getattr(core, "get_locked_policy", lambda: None)()
        if locked:
            self.info.setText(
                "Classroom policy is locked by the teacher.\n"
                f"Min voxels: {locked.get('min_voxels')}\n"
                f"Tolerance: {locked.get('tolerance')}\n"
                "Solo settings below are disabled while you are in a classroom."
            )
            self.b_minvox.setEnabled(False)
            self.b_tol.setEnabled(False)
        else:
            self.info.setText(
                "Solo practice settings (offline).\n"
                "These affect your local practice only."
            )
            self.b_minvox.setEnabled(True)
            self.b_tol.setEnabled(True)

        cur = str(core.cfg_get("update_json_url", "") or "").strip()
        if cur:
            self.b_update_url.setText("Set (configured)")
        else:
            self.b_update_url.setText("Set")

    def _set_minvox(self):
        cur = int(core.cfg_get("solo_min_voxels", core.DEFAULT_MIN_VOXELS) or core.DEFAULT_MIN_VOXELS)
        v, ok = QInputDialog.getInt(self, "Min voxels", "Minimum lesion voxels (solo):", cur, 1, 10_000, 1)
        if not ok:
            return
        core.cfg_set("solo_min_voxels", int(v))
        self.refresh()
        self.app.toast("Saved.")

    def _set_tol(self):
        cur = int(core.cfg_get("solo_tolerance", core.DEFAULT_TOLERANCE) or core.DEFAULT_TOLERANCE)
        v, ok = QInputDialog.getInt(self, "Tolerance", "Voxel mismatch tolerance (solo):", cur, 0, 1_000_000, 10)
        if not ok:
            return
        core.cfg_set("solo_tolerance", int(v))
        self.refresh()
        self.app.toast("Saved.")

    def _set_update_url(self):
        cur = str(core.cfg_get("update_json_url", "") or "")
        url, ok = QInputDialog.getText(
            self,
            "Update feed",
            "Enter the URL to latest.json (GitHub Pages / internal HTTP):",
            text=cur,
        )
        if not ok:
            return
        url = str(url or "").strip()
        core.cfg_set("update_json_url", url)
        self.refresh()
        if url:
            QMessageBox.information(self, "Updates", "Update URL saved.")
        else:
            QMessageBox.information(self, "Updates", "Update URL cleared.")

    def _check_updates(self):
        url = str(core.cfg_get("update_json_url", "") or "").strip()
        if not url:
            QMessageBox.information(self, "Updates", "No update URL set.\nSet it first in Settings.")
            return

        try:
            info = upd.check_for_update(url, core.APP_VERSION)
        except Exception as e:
            QMessageBox.critical(self, "Updates", f"Update check failed:\n{e}")
            return

        if not info:
            QMessageBox.information(self, "Updates", "You are up to date.")
            return

        QMessageBox.information(
            self,
            "Update available",
            f"New version available: {info.version}\n\n{info.notes}\n\n"
            "Download will be staged in your updates folder.",
        )
        try:
            staged = upd.download_update(info)
            QMessageBox.information(self, "Update staged", f"Downloaded to:\n{staged}\n\nRestart the app to apply manually.")
        except Exception as e:
            QMessageBox.critical(self, "Download failed", str(e))
