from __future__ import annotations

from PySide6.QtWidgets import QApplication
import lt_core as core


def apply_qss(app: QApplication) -> None:
    qss = f"""
    QWidget {{
        background-color: {core.BG0};
        color: {core.TEXT};
        font-size: 13px;
        font-family: "SF Pro Display","SF Pro Text","Helvetica Neue","Inter","Segoe UI","Arial";
    }}

    QLabel#AppTitle {{
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 0.3px;
    }}

    QWidget#TopBar {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {core.PANEL2}, stop:1 {core.PANEL});
        border: 1px solid {core.STROKE};
        border-radius: 14px;
    }}

    QWidget#Sidebar {{
        background: {core.PANEL2};
        border: 1px solid {core.STROKE};
        border-radius: 14px;
    }}

    QListWidget {{
        background: transparent;
        border: none;
        outline: none;
    }}

    QListWidget::item {{
        padding: 12px 12px;
        margin: 4px 4px;
        border-radius: 12px;
        color: {core.MUTED};
    }}

    QListWidget::item:selected {{
        background: rgba(226, 0, 26, 0.16);
        color: {core.TEXT};
        border: 1px solid rgba(226, 0, 26, 0.45);
    }}

    QLabel#H1 {{
        font-size: 28px;
        font-weight: 900;
        letter-spacing: 0.2px;
    }}

    QLabel#Muted {{
        color: {core.MUTED};
    }}

    QLabel#Pill {{
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.04);
        border: 1px solid {core.STROKE};
        color: {core.MUTED};
        font-weight: 700;
    }}

    QPushButton#BtnGhost {{
        background: {core.BTN};
        border: 1px solid {core.STROKE};
        border-radius: 12px;
        padding: 8px 12px;
        font-weight: 800;
        color: {core.TEXT};
    }}
    QPushButton#BtnGhost:hover {{
        background: {core.BTN_H};
    }}

    QPushButton#BtnPrimary {{
        background: {core.EPFL_RED};
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 12px;
        padding: 8px 12px;
        font-weight: 900;
        color: {core.TEXT};
    }}
    QPushButton#BtnPrimary:hover {{
        background: #ff0020;
    }}

    QPushButton#BtnDanger {{
        background: rgba(226,0,26,0.12);
        border: 1px solid rgba(226,0,26,0.50);
        border-radius: 12px;
        padding: 8px 12px;
        font-weight: 900;
        color: {core.TEXT};
    }}
    QPushButton#BtnDanger:hover {{
        background: rgba(226,0,26,0.18);
    }}

    QLineEdit {{
        background: rgba(255,255,255,0.03);
        border: 1px solid {core.STROKE};
        border-radius: 12px;
        padding: 10px 12px;
        color: {core.TEXT};
    }}

    QTableWidget {{
        background: rgba(255,255,255,0.02);
        border: 1px solid {core.STROKE};
        border-radius: 14px;
        gridline-color: rgba(255,255,255,0.06);
    }}

    QHeaderView::section {{
        background: rgba(255,255,255,0.02);
        border: none;
        padding: 8px 10px;
        color: {core.MUTED};
        font-weight: 900;
    }}
    """
    app.setStyleSheet(qss)
