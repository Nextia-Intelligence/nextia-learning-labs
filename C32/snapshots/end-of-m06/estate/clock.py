"""The estate's clock. Real time, except in a replayed scenario, which moves it through a replayed month.

Every module that needs "now" (the registry's events, budget windows, token times) asks here, so that a
replay of a month in a few minutes gives the same windows and dates as the real month would.
"""

from datetime import datetime, timezone

_fixed: datetime | None = None


def now() -> datetime:
    return _fixed or datetime.now(timezone.utc)


def iso() -> str:
    return now().isoformat(timespec="seconds")


def set_replay_time(when: datetime | None) -> None:
    """For replayed scenarios only: every later now() returns `when` (None: real time again)."""
    global _fixed
    _fixed = when
