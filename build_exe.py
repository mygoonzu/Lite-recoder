from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(command: list[str]) -> None:
    print(">", " ".join(command))
    subprocess.check_call(command, cwd=ROOT)


def main() -> int:
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--windowed",
            "--name",
            "Win11Recorder",
            "--add-data",
            "config.json;.",
            "app.py",
        ]
    )
    print("\nBuild xong. Xem file tai dist/Win11Recorder/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
