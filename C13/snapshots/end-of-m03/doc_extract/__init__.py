"""doc-extract: read Larkfield's documents and keep the source of every value."""

import os
from pathlib import Path

__version__ = "1.0.0"


def _load_env(path: Path = Path(".env")) -> None:
    """Read KEY=value lines from .env into the environment (values already set win)."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            if value.strip():
                os.environ.setdefault(key.strip(), value.strip())


_load_env()
