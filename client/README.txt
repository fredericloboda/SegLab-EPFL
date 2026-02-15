LT Trainer (EPFL) — modular client folder

Run:
  cd client
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python startt_trainer.py

Public (offline) materials shipped in:
  client/resources/materials_public/

User data created here:
  ~/LTTrainerEPFL_UserData/

SMB share URL (open in Finder):
  smb://sv-nas1.rcp.epfl.ch/Hummel-Lab

IMPORTANT: in the app you must select the *mounted* folder path (not smb://):
  macOS: /Volumes/Hummel-Lab/...
  Windows: X:\...



UPDATES (real-app style)
- Set update feed URL in Settings (points to latest.json).
- Press 'Check for updates'. The update is downloaded in background and applied on restart.
- For production: host latest.json + zip on GitHub Releases or an EPFL HTTP server.
