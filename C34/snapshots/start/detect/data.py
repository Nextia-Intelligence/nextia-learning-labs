"""Read the payments: all of them once, then the days a command needs."""
from functools import lru_cache
from pathlib import Path

import pandas as pd

COLUMNS = ["payment_id", "ts", "customer_id", "account_type", "region", "amount", "currency", "country",
           "device_id", "device_type", "merchant_category", "hour"]


@lru_cache(maxsize=2)
def _read(path: str) -> pd.DataFrame:
    p = pd.read_csv(path, parse_dates=["ts"])
    missing = set(COLUMNS) - set(p.columns)
    if missing:
        raise SystemExit(f"{path} has no column {sorted(missing)}. Is it the course's payments file?")
    return p


def payments(data_dir: Path) -> pd.DataFrame:
    """All payments, from data/payments.csv.gz (or a smaller payments.csv in the same folder)."""
    for name in ("payments.csv.gz", "payments.csv"):
        path = Path(data_dir) / name
        if path.exists():
            return _read(str(path.resolve()))
    raise SystemExit(f"No payments file in {data_dir}/. Run: python scripts/get_data.py")


def window(p: pd.DataFrame, first_day, last_day) -> pd.DataFrame:
    """The payments from the start of first_day to the end of last_day."""
    a, b = pd.Timestamp(first_day), pd.Timestamp(last_day) + pd.Timedelta("1D")
    return p[(p.ts >= a) & (p.ts < b)]
