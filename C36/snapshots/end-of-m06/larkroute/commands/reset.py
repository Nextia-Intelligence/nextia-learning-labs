"""route reset: go back to the start. Deletes what the commands wrote (models/, runs/, queue/), puts back the
course's configuration files, and downloads any data file that is missing or changed."""

import shutil
import subprocess
import sys
from pathlib import Path

from larkroute import data

ROOT = Path(__file__).resolve().parents[2]
DEFAULTS = Path(__file__).resolve().parents[1] / "defaults"
OUTPUTS = ["models", "runs", "queue"]


def run(args):
    removed = [d for d in OUTPUTS if (ROOT / d).exists()]
    for d in removed:
        shutil.rmtree(ROOT / d)
    restored = []
    for f in sorted(DEFAULTS.glob("*.json")):
        target = ROOT / "config" / f.name
        if not target.exists() or target.read_bytes() != f.read_bytes():
            shutil.copyfile(f, target)
            restored.append(f.name)
    bad = data.check()
    if bad:
        subprocess.run([sys.executable, str(ROOT / "get_data.py")], check=True)
        bad = data.check()
    state = "all files are right" if not bad else "still wrong: " + ", ".join(bad)
    print(f"Reset: removed {', '.join(removed) or 'nothing'}; "
          f"config restored: {', '.join(restored) or 'none changed'}; data: {state}.")


def add(sub):
    p = sub.add_parser("reset", help="delete outputs, restore the configuration, check the data")
    p.set_defaults(func=run)
