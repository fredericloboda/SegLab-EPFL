from __future__ import annotations
from pathlib import Path
import shutil
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QFileDialog, QMessageBox
import lt_core as core
from lt_utils import open_default
from ui.widgets import btn, h1, muted

class MaterialsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        v = QVBoxLayout(self)
        v.setContentsMargins(44, 34, 44, 34)
        v.setSpacing(12)

        v.addWidget(h1("Materials"))
        v.addWidget(muted("""Public materials are always available offline.
You can also add your own local PDFs/PPTX, and (optionally) protected materials from the SMB classroom."""))

        self.list = QListWidget()
        v.addWidget(self.list, 1)

        row = QHBoxLayout()
        row.setSpacing(10)
        self.b_add = btn("Add local material…", "primary")
        self.b_open = btn("Open", "ghost")
        self.b_folder = btn("Open local materials folder", "ghost")
        row.addWidget(self.b_add)
        row.addWidget(self.b_open)
        row.addWidget(self.b_folder)
        row.addStretch(1)
        v.addLayout(row)

        self.b_add.clicked.connect(self._add)
        self.b_open.clicked.connect(self._open)
        self.b_folder.clicked.connect(lambda: open_default(core.LOCAL_MATERIALS))

        self.refresh()

    def refresh(self):
        self.list.clear()
        items = []

        core.PUBLIC_MATERIALS_DIR.mkdir(parents=True, exist_ok=True)
        for p in sorted([x for x in core.PUBLIC_MATERIALS_DIR.iterdir() if x.is_file()], key=lambda x: x.name.lower()):
            items.append(("Public", p))

        core.LOCAL_MATERIALS.mkdir(parents=True, exist_ok=True)
        for p in sorted([x for x in core.LOCAL_MATERIALS.iterdir() if x.is_file()], key=lambda x: x.name.lower()):
            items.append(("Local", p))

        if self.app.mode in ("student", "teacher") and self.app.share_root and self.app.class_code:
            prot = self.app.share_root / "classrooms" / self.app.class_code / "materials_protected"
            if prot.exists():
                for p in sorted([x for x in prot.iterdir() if x.is_file()], key=lambda x: x.name.lower()):
                    items.append(("Protected", p))

        if not items:
            self.list.addItem("(no materials)")
            self._items = []
            return

        self._items = items
        for group, p in items:
            self.list.addItem(f"[{group}] {p.name}")

    def _add(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Add material", str(Path.home()), "Docs (*.pdf *.pptx *.ppt);;All files (*)")
        if not fp:
            return
        src = Path(fp)
        dst = core.LOCAL_MATERIALS / src.name
        try:
            shutil.copy2(src, dst)
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, core.APP_NAME, f"Copy failed: {e}")

    def _open(self):
        it = self.list.currentRow()
        if it < 0 or it >= len(getattr(self, "_items", [])):
            return
        _, p = self._items[it]
        if p.exists():
            open_default(p)
