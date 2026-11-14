import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    separator = os.pathsep
    output_directory = ROOT / "dist" / "backend"
    if output_directory.exists():
        shutil.rmtree(output_directory)

    data_dirs = (
        ("frontend/templates", "frontend/templates"),
        ("frontend/static", "frontend/static"),
        ("store.ico", "."),
    )
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name",
        "DukaanDeskBackend",
        "--distpath",
        str(output_directory),
        "--workpath",
        str(ROOT / "build" / "pyinstaller"),
        "--specpath",
        str(ROOT / "build" / "pyinstaller"),
        "--paths",
        str(ROOT),
    ]
    for source, destination in data_dirs:
        command.extend(
            [
                "--add-data",
                f"{ROOT / source}{separator}{destination}",
            ]
        )
    command.append(str(ROOT / "app.py"))
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
