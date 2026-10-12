"""The operations files (operations/*.toml): the inventory, the objectives and, from Module 2,
the release manifests. TOML is read with Python's own tomllib."""

import tomllib
from pathlib import Path

DEFAULT = Path("operations")


def load(name: str, folder: str | Path = DEFAULT) -> dict:
    path = Path(folder) / name
    if not path.exists():
        raise FileNotFoundError(f"no file {path} (run ops from the project folder)")
    with path.open("rb") as f:
        return tomllib.load(f)
