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
    alerts_dir: Path = field(default_factory=lambda: Path(_env("DETECT_ALERTS", "alerts")))
    # alerts a day that the review team can read (Sofia's team: 50)
    budget: int = field(default_factory=lambda: int(_env("DETECT_BUDGET", "50")))
    # "budget": every day, the `budget` most unusual alerts. "fixed": every alert above the score threshold
    # learned from the training days (no daily limit).
    policy: str = field(default_factory=lambda: _env("DETECT_POLICY", "budget"))
    history_days: int = 60          # how far back the behaviour features look
    snooze_days: int = 7            # after a "not fraud" review, the customer's alerts wait this many days
