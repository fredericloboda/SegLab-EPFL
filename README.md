# SegLab (EPFL)

SegLab is a desktop trainer for lesion segmentation and case-based practice (Qt / PySide6).  
It supports **offline built-in cases**, local workspaces, and a simple **auto-update** flow via a hosted `latest.json`.

---

## Quick start (run from source)

### macOS / Linux
```bash
cd seglab
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python3 startt_trainer.py
