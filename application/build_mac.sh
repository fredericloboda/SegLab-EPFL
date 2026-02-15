#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Clean build venv
rm -rf .venv_build
python3 -m venv .venv_build
source .venv_build/bin/activate

python -m pip install -U pip
python -m pip install PySide6 numpy nibabel pyinstaller requests
python -m pip uninstall -y PyQt5 PyQt6 || true

# Build (onedir .app)
python -m PyInstaller --noconfirm --clean --windowed \
  --name "LTTrainerEPFL" \
  --exclude-module PyQt5 --exclude-module PyQt6 \
  startt_trainer.py

echo "Built: dist/LTTrainerEPFL.app"
echo "Zip with: cd dist && ditto -c -k --sequesterRsrc --keepParent LTTrainerEPFL.app LTTrainerEPFL-mac.zip"
