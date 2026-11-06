"""People and forecasts: a planner may replace the job's order. The job keeps both numbers and the reason,
and measures later whether the change helped (forecast value added, FVA).

An overrides file has one row per change: week, product_id, region, order, reason, who. FVA of one override =
the cost of the job's order minus the cost of the planner's order, both against the 14 days that followed.
Positive: the override saved money. Negative: it cost money.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .store import planned_weeks, week_dir

COLUMNS = ["week", "product_id", "region", "order", "reason", "who"]


def read(path):
    if path is None or not Path(path).exists():
        return pd.DataFrame(columns=COLUMNS)
    o = pd.read_csv(path, parse_dates=["week"])
    missing = set(COLUMNS) - set(o.columns)
    if missing:
        raise SystemExit(f"{path} has no column {sorted(missing)}")
    if o["reason"].fillna("").str.strip().eq("").any():
        raise SystemExit(f"{path}: every override needs a reason")
    return o


def for_week(overrides, week):
    return overrides[overrides["week"] == week].reset_index(drop=True)


def apply(orders, week_overrides):
    """Adds the columns job_order, override, reason and who; `order` becomes the order that is placed."""
    o = orders.rename(columns={"order": "job_order"})
    w = week_overrides[["product_id", "region", "order", "reason", "who"]].rename(columns={"order": "override"})
    o = o.merge(w, on=["product_id", "region"], how="left")
    o["override"] = pd.to_numeric(o["override"]).astype("Int64")
    o["order"] = o["override"].fillna(o["job_order"]).astype(int)
    return o


def _cost(order, sold, price):
    short = np.maximum(sold - order, 0)
    over = np.maximum(order - sold, 0)
    return (short * config.LOST_SALE_SHARE + over * config.LEFT_OVER_SHARE) * price


def value_added(store, data_dir):
    """FVA of every override in the store whose 14 days have passed."""
    sales = pd.read_csv(Path(data_dir) / "demand.csv.gz", parse_dates=["date"])
    rows = []
    for week in planned_weeks(store):
        days = pd.date_range(week, periods=config.HORIZON_DAYS, freq="D")
        if sales["date"].max() < days[-1]:
            continue
        o = pd.read_csv(week_dir(store, week) / "orders.csv")
        o = o[o["override"].notna()] if "override" in o else o.iloc[0:0]
        if o.empty:
            continue
        sold = (sales[sales["date"].isin(days)].groupby(["product_id", "region"])["sales"].sum()
                .rename("sold").reset_index())
        o = o.merge(sold, on=["product_id", "region"], how="left").fillna({"sold": 0})
        o["job_cost"] = _cost(o["job_order"], o["sold"], o["base_price"]).round(2)
        o["override_cost"] = _cost(o["override"], o["sold"], o["base_price"]).round(2)
        o["fva_usd"] = (o["job_cost"] - o["override_cost"]).round(2)
        o.insert(0, "week", str(week.date()))
        rows.append(o[["week", "product_id", "region", "reason", "who", "job_order", "override", "sold",
                       "job_cost", "override_cost", "fva_usd"]])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
