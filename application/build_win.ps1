\
    # build_win.ps1 (run in PowerShell)
    Set-StrictMode -Version Latest
    $ErrorActionPreference = "Stop"

    cd $PSScriptRoot

    if (Test-Path ".venv_build") { Remove-Item -Recurse -Force ".venv_build" }
    python -m venv .venv_build
    .\.venv_build\Scripts\Activate.ps1

    python -m pip install -U pip
    python -m pip install PySide6 numpy nibabel pyinstaller requests
    python -m pip uninstall -y PyQt5 PyQt6

    python -m PyInstaller --noconfirm --clean --windowed `
      --name "LTTrainerEPFL" `
      --exclude-module PyQt5 --exclude-module PyQt6 `
      startt_trainer.py

    Write-Host "Built: dist\LTTrainerEPFL\LTTrainerEPFL.exe (onedir)"
    Write-Host "Zip the dist\LTTrainerEPFL folder and send it."
