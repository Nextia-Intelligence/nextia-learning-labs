"""recs reset: back to the start (delete outputs/, check the data)."""

import shutil

from .. import data
from ..paths import outputs_dir

NAME = "reset"
HELP = "Delete outputs/ (models, runs, suggestion lists, deletion requests) and check the data files."


def add(p):
    pass


def run(args):
    out = outputs_dir()
    n = sum(1 for p in out.rglob("*") if p.is_file())
    shutil.rmtree(out)
    bad = data.verify()
    state = "all files are right" if not bad else f"missing or changed: {', '.join(bad)}"
    print(f"Reset: removed {n} files from {out}/; data: {len(data.checksums())} files, {state}.")
