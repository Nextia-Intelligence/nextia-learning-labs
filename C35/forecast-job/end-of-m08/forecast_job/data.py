"""Get the data that the job may use for one week, and check it before any forecast."""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import config


@dataclass
class Inputs:
    """Everything the job knows on the Monday of `week`: the history up to the Sunday before, and the inputs
    that are planned in advance (promotions and price changes)."""

    week: pd.Timestamp
    demand: pd.DataFrame
    tickets: pd.DataFrame
    products: pd.DataFrame
    promotions: pd.DataFrame
    price_changes: pd.DataFrame
    problems: list = field(default_factory=list)


class DataError(Exception):
    """The data is not safe to forecast from. The job stops and writes nothing."""


def monday(text):
    week = pd.Timestamp(text)
    if week.dayofweek != 0:
        raise SystemExit(f"{week.date()} is not a Monday. The job runs for a week that starts on a Monday.")
    return week


def load(data_dir, week):
    """Read the data folder and keep only what was known on the Monday `week` (the replay of a real week)."""
    data_dir = Path(data_dir)
    if not (data_dir / "demand.csv.gz").exists():
        raise SystemExit(f"No data in {data_dir}. Run: python get_data.py")
    last = week - pd.Timedelta(days=1)
    demand = pd.read_csv(data_dir / "demand.csv.gz", parse_dates=["date"])
    tickets = pd.read_csv(data_dir / "tickets_hourly.csv.gz", parse_dates=["timestamp"])
    return Inputs(
        week=week,
        demand=demand[demand["date"] <= last].reset_index(drop=True),
        tickets=tickets[tickets["timestamp"] < week].reset_index(drop=True),
        products=pd.read_csv(data_dir / "products.csv", parse_dates=["launch_date"]),
        promotions=pd.read_csv(data_dir / "promotions.csv", parse_dates=["start", "end"]),
        price_changes=pd.read_csv(data_dir / "price_changes.csv", parse_dates=["date"]),
    )


def check(inputs):
    """Check the data. Raises DataError for a problem that makes every forecast wrong; returns the warnings
    (and keeps them in inputs.problems) for problems that the job can handle."""
    d, last = inputs.demand, inputs.week - pd.Timedelta(days=1)
    if d.empty:
        raise DataError("no sales rows before this week")
    if d["date"].max() < last:
        raise DataError(f"the sales feed is late: the last day is {d['date'].max().date()}, expected {last.date()}")
    if d.duplicated(["date", "region", "product_id"]).any():
        n = int(d.duplicated(["date", "region", "product_id"]).sum())
        raise DataError(f"{n} duplicated rows (the same product, region and day twice)")
    if (d["sales"] < 0).any():
        raise DataError(f"{int((d['sales'] < 0).sum())} rows with negative sales")
    if inputs.tickets.empty or inputs.tickets["timestamp"].max() < inputs.week - pd.Timedelta(hours=1):
        raise DataError("the ticket feed is late: no tickets for the last hour before this week")
    warnings = []
    recent = pd.date_range(last - pd.Timedelta(days=27), last, freq="D")
    missing = sorted(set(recent) - set(d["date"].unique()))
    for day in missing:
        warnings.append(f"no sales rows for {day.date()}: filled with the same weekday one week before and after")
    week_rows = d[d["date"] > last - pd.Timedelta(days=7)]
    share = float(week_rows["stock_out"].mean()) if len(week_rows) else 0.0
    if share > config.MAX_STOCK_OUT_SHARE:
        warnings.append(f"{share:.0%} of last week's rows are stock-outs: sales there are lower than demand")
    inputs.problems = warnings
    return warnings
