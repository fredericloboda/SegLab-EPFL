from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QPushButton

def btn(text: str, kind: str = "ghost") -> QPushButton:
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setMinimumHeight(40)
    b.setObjectName({"primary":"BtnPrimary","ghost":"BtnGhost","danger":"BtnDanger"}.get(kind,"BtnGhost"))
    return b

def h1(text: str) -> QLabel:
    l = QLabel(text); l.setObjectName("H1"); return l

def muted(text: str) -> QLabel:
    l = QLabel(text); l.setObjectName("Muted"); l.setWordWrap(True); return l

def pill(text: str) -> QLabel:
    l = QLabel(text)
    l.setObjectName("Pill")
    l.setAlignment(Qt.AlignCenter)
    return l


from PySide6.QtWidgets import QWidget, QVBoxLayout

class Card(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._v = QVBoxLayout(self)
        self._v.setContentsMargins(14, 14, 14, 14)
        self._v.setSpacing(10)

    def body(self) -> QVBoxLayout:
        return self._v

