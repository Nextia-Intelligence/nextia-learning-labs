"""Watch the forecast: compare the first week of a plan with what was sold, by category, and raise a bias
alarm when a category is off in the same direction two weeks in a row.

bias % = 100 x (forecast - sales) / sales. Negative: the forecast was too low (risk of stock-outs);
positive: too high (left-over stock). The alarm needs at least 200 units sold in the category that week, so
that a few units of a slow category do not raise it.
"""

from pathlib import Path

import pandas as pd

from .store import week_dir

ALARM_PCT = 20.0
ALARM_WEEKS = 2
MIN_UNITS = 200


def check_week(store, data_dir, week):
    """Bias by category of the plan of `week` over its first 7 days. Needs the sales of those 7 days."""
    d = week_dir(store, week)
    if not (d / "run.json").exists():
        raise SystemExit(f"The week of {week.date()} has no plan in {store}/. "
                         f"Plan it first: python -m forecast_job run --week {week.date()}")
    fc = pd.read_csv(d / "forecast.csv", parse_dates=["ds"])
    sales = pd.read_csv(Path(data_dir) / "demand.csv.gz", parse_dates=["date"])
    days = pd.date_range(week, periods=7, freq="D")
    if sales["date"].max() < days[-1]:
        raise SystemExit(f"The sales of the week of {week.date()} are not complete yet: "
                         f"check it after {days[-1].date()}.")
    # compare only the days that have sales rows (a day the feed dropped is left out on both sides)
    days = days[days.isin(sales["date"].unique())]
    products = pd.read_csv(Path(data_dir) / "products.csv")[["product_id", "category"]]
    f = fc[fc["ds"].isin(days)].merge(products, on="product_id").groupby("category")["yhat"].sum()
    s = sales[sales["date"].isin(days)].merge(products, on="product_id").groupby("category")["sales"].sum()
    out = pd.DataFrame({"forecast": f.round(1), "sales": s}).fillna(0)
    out["bias_pct"] = (100 * (out["forecast"] - out["sales"]) / out["sales"].where(out["sales"] > 0)).round(1)
    out = out.reset_index().rename(columns={"index": "category"})
    out.insert(0, "week", str(week.date()))
    out["days"] = len(days)
    out.to_csv(d / "check.csv", index=False)
    return out


def alarms(store, week):
    """The categories whose bias was beyond the limit, in the same direction, for ALARM_WEEKS checks."""
    weeks = [week - pd.Timedelta(weeks=k) for k in range(ALARM_WEEKS)]
    checks = []
    for w in weeks:
        f = week_dir(store, w) / "check.csv"
        if not f.exists():
            return []
        checks.append(pd.read_csv(f).set_index("category"))
    out = []
    for cat in checks[0].index:
        rows = [c.loc[cat] for c in checks if cat in c.index]
        if len(rows) < ALARM_WEEKS or any(r["sales"] < MIN_UNITS or pd.isna(r["bias_pct"]) for r in rows):
            continue
        low = all(r["bias_pct"] <= -ALARM_PCT for r in rows)
        high = all(r["bias_pct"] >= ALARM_PCT for r in rows)
        if low or high:
            out.append({"category": cat, "direction": "too low" if low else "too high",
                        "bias_pct": [float(r["bias_pct"]) for r in rows][::-1],
                        "weeks": [str(w.date()) for w in weeks][::-1]})
    return out


def describe(alarm):
    pcts = " and ".join(f"{b:+.0f}%" for b in alarm["bias_pct"])
    return (f"BIAS ALARM {alarm['category']}: the forecast was {alarm['direction']} {ALARM_WEEKS} weeks in a row "
            f"({pcts}, weeks of {', '.join(alarm['weeks'])}). Look for the cause before the next order "
            "(a season that starts early, a stock-out, a price change), then refit or change the method.")
