"""Settings of the job. Each one can be changed with an environment variable."""
import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name, default):
    return os.environ.get(name, default)


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(_env("DETECT_DATA", "data")))
    state_dir: Path = field(default_factory=lambda: Path(_env("DETECT_STATE", "state")))
    budget: int = field(default_factory=lambda: int(_env("DETECT_BUDGET", "50")))
    history_days: int = 60          # how far back the behaviour features look
