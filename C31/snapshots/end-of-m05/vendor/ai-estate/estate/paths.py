"""Where the estate keeps its files. The practice state (databases, keys, logs) is in state/, which is
git-ignored: delete it, or run `python -m estate reset`, to start again."""

import os
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
CONFIG = Path(os.environ.get("ESTATE_CONFIG", PROJECT / "config"))
REGISTRATIONS = Path(os.environ.get("ESTATE_REGISTRATIONS", PROJECT / "registrations"))
DATA = PROJECT / "data"
EVIDENCE = PROJECT / "evidence"


def state() -> Path:
    """The practice state folder (ESTATE_STATE, default state/). Read each time: the tests change it."""
    path = Path(os.environ.get("ESTATE_STATE", PROJECT / "state"))
    path.mkdir(parents=True, exist_ok=True)
    return path
