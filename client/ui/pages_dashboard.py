from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from ui.widgets import btn, h1, muted

class DashboardPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        v = QVBoxLayout(self)
        v.setContentsMargins(44, 34, 44, 34)
        v.setSpacing(14)

        v.addWidget(h1("Dashboard"))
        self.sub = muted("")
        v.addWidget(self.sub)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.b_materials = btn("Materials", "ghost")
        self.b_practice = btn("Practice", "ghost")
        self.b_progress = btn("Progress", "ghost")
        self.b_connect = btn("Connect", "primary")
        row.addWidget(self.b_materials)
        row.addWidget(self.b_practice)
        row.addWidget(self.b_progress)
        row.addWidget(self.b_connect)
        row.addStretch(1)
        v.addLayout(row)
        v.addStretch(1)

        self.b_materials.clicked.connect(lambda: self.app.goto("Materials"))
        self.b_practice.clicked.connect(lambda: self.app.goto("Practice"))
        self.b_progress.clicked.connect(lambda: self.app.goto("Progress"))
        self.b_connect.clicked.connect(lambda: self.app.goto("Connect"))

    def refresh(self):
        if self.app.mode == "solo":
            self.sub.setText("""Solo (offline)
• Add sandbox cases in Practice
• Settings editable
• Attempts saved locally""")
        elif self.app.mode == "student":
            pol = self.app.locked_policy or {}
            self.sub.setText(f"""Student classroom
• Class: {self.app.class_code or '—'}
• Policy locked: min_voxels={pol.get('min_voxels')} | tolerance={pol.get('tolerance')}
• Sync cases in Practice; attempts are written to the share.""")
        elif self.app.mode == "teacher":
            self.sub.setText(f"""Teacher
• Share: {self.app.share_root}
• Class: {self.app.class_code or '—'}
• Create classroom, upload cases, view cohort dashboard.""")
        else:
            self.sub.setText("Start at Gate.")
