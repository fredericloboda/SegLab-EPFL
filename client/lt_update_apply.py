# lt_update_apply.py — apply update zip (macOS-friendly). Updates are applied on restart.
from __future__ import annotations
import shutil, subprocess, sys, tempfile, time, zipfile
from pathlib import Path

def die(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)

def find_current_app() -> Path | None:
    exe = Path(sys.executable).resolve()
    p = exe
    while p != p.parent:
        if p.suffix == ".app":
            return p
        p = p.parent
    return None

def main():
    if len(sys.argv) != 2:
        die("Usage: lt_update_apply.py <staged_zip>")
    staged_zip = Path(sys.argv[1]).resolve()
    if not staged_zip.exists():
        die(f"Staged zip not found: {staged_zip}")

    time.sleep(1.2)  # allow app to exit

    tmp = Path(tempfile.mkdtemp(prefix="lt_update_"))
    with zipfile.ZipFile(staged_zip, "r") as z:
        z.extractall(tmp)

    apps = list(tmp.rglob("*.app"))
    if not apps:
        die("No .app found inside update zip.")
    new_app = apps[0]

    cur_app = find_current_app()
    if cur_app and cur_app.exists():
        target = cur_app
        backup = target.with_name(target.name + ".bak")
        try:
            if backup.exists():
                shutil.rmtree(backup, ignore_errors=True)
            shutil.move(str(target), str(backup))
            shutil.move(str(new_app), str(target))
            shutil.rmtree(backup, ignore_errors=True)
            subprocess.Popen(["open", str(target)])
        except Exception as e:
            die(f"Update failed: {e}")
    else:
        subprocess.Popen(["open", str(new_app)])

if __name__ == "__main__":
    main()
