from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from ui.widgets import btn, h1, muted

class GatePage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        v = QVBoxLayout(self)
        v.setContentsMargins(44, 34, 44, 34)
        v.setSpacing(18)

        v.addWidget(h1("Lesion Segmentation Trainer"))
        v.addWidget(muted("""Choose how you want to use the trainer:
• Solo (offline): practice + your own settings
• Student: join classroom (policy locked)
• Teacher: PIN + classroom creation + uploads
"""))

        row = QHBoxLayout()
        row.setSpacing(12)
        b1 = btn("Solo (offline)", "primary")
        b2 = btn("Student (join classroom)", "ghost")
        b3 = btn("Teacher (PIN)", "ghost")
        row.addWidget(b1)
        row.addWidget(b2)
        row.addWidget(b3)
        row.addStretch(1)
        v.addLayout(row)
        v.addStretch(1)

        b1.clicked.connect(self.app.enter_solo)
        b2.clicked.connect(lambda: self.app.goto("Connect"))
        b3.clicked.connect(lambda: self.app.goto("Teacher"))

    def refresh(self):
        pass
