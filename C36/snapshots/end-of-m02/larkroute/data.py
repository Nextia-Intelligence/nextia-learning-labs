"""Read the Larkfield inbox (data/) and its labels.

The data is synthetic: it was made for the course and has no real people. Run `python get_data.py` once to
download it into data/ (or set LARKROUTE_DATA to another folder).
"""

import hashlib
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ["orders", "delivery", "returns_refunds", "billing", "product", "account", "needs_person"]


def data_dir() -> Path:
    return Path(os.environ.get("LARKROUTE_DATA", ROOT / "data"))


def _read(name: str) -> pd.DataFrame:
    path = data_dir() / name
    if not path.exists():
        raise SystemExit(f"No {path}. Run: python get_data.py")
    return pd.read_csv(path, keep_default_na=False, na_values=[""])


def messages(split: str | None = None) -> pd.DataFrame:
    """The 10,000 labelled messages; split is "train", "validation" or "test" (None: all of them)."""
    df = _read("messages.csv")
    if split is not None:
        if split not in ("train", "validation", "test"):
            raise ValueError(f"unknown split {split!r}")
        df = df[df["split"] == split]
    return df.reset_index(drop=True)


def launch_month() -> pd.DataFrame:
    """The 2,000 messages of the launch month, with no labels."""
    return _read("launch_month.csv")


def check() -> list[str]:
    """The data files whose checksum is not the one in SHA256SUMS (an empty list: all good)."""
    sums = data_dir() / "SHA256SUMS"
    if not sums.exists():
        return ["SHA256SUMS"]
    bad = []
    for line in sums.read_text().splitlines():
        expected, name = line.split()
        path = data_dir() / name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            bad.append(name)
    return bad
