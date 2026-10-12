"""Settings from environment variables (and the project's .env file). One place, read once.

The database password is inside DATABASE_URL: the field has repr=False, so printing the settings
never shows it.
"""

import os
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default="", repr=False)
    today: str = ""                      # ASSISTANT_TODAY: the course's "today"; empty = the real date

    def today_date(self) -> str:
        return self.today or date.today().isoformat()


def load_env_file(path: Path | None = None) -> None:
    """Read KEY=value lines from .env (variables already set in the environment win)."""
    path = path or PROJECT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def from_env(env: dict | None = None) -> Settings:
    e = env if env is not None else os.environ
    s = Settings()

    def get(name: str, default):
        return e.get(name, default) or default

    return Settings(
        database_url=get("DATABASE_URL", s.database_url),
        today=get("ASSISTANT_TODAY", s.today),
    )


@lru_cache
def settings() -> Settings:
    load_env_file()
    return from_env()
