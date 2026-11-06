"""backtest.py: the rolling-origin backtest and the backtest table of the forecasting course.

One function tests any forecaster the same way: it cuts the history at several origins (the last day the
forecaster may see), asks for a forecast of the next `h` periods, and keeps the real values next to it.
Another function scores the result with the columns of the course's backtest table.

    import backtest as bt
    origins = bt.origins("2026-03-15", n=13, every="28D")
    fc = bt.backtest(df, my_forecaster, h=14, origins=origins)
    row = bt.score(fc, df, method="my method", season=7, cost=bt.stock_cost(prices))
    bt.show([row])

The data is in the "long" format of the Nixtla libraries: one row per series and period, with the columns
unique_id (the series), ds (the date or hour) and y (the value). Other columns are inputs that a forecaster
may use (a price, a promotion flag).

A forecaster is a function forecaster(train, h, future) that returns one row per series and period of the
next h periods, with the columns unique_id, ds and yhat (and, for a range, q10, q50, q90 ... as numbers
between 0 and 1 times 100). `train` holds the rows up to the origin. `future` holds the rows of the next h
periods without y: only the inputs that are known in advance (calendar, price, promotion).

Refit rule: a function is fitted again at every origin (refit_every=1, the course default). An object with
fit(train) and predict(train, h, future) is fitted at the first origin and then every `refit_every`
origins; between them, predict() gets the newer history but the old fit.

Free to use under the MIT licence. Part of Nextia Learning's forecasting course (learning.nextia-ai.com).
"""

import time

import numpy as np
import pandas as pd

QUANTILE_PREFIX = "q"
TABLE_COLUMNS = ["method", "horizon", "MASE", "WAPE %", "bias %", "pinball", "fit s", "cost $"]


def origins(last, n, every="28D"):
    """n origins, the last one on `last`, `every` apart (oldest first)."""
    last = pd.Timestamp(last)
    step = pd.Timedelta(every)
    return [last - step * k for k in range(n - 1, -1, -1)]


def _periods(df):
    """The step between two periods of the data (a day or an hour)."""
    ds = np.sort(df["ds"].unique())
    return pd.Timedelta(np.diff(ds).min())


def backtest(df, forecaster, h, origins, refit_every=1):
    """Forecast h periods after every origin and return the forecasts next to the real values.

    Returns one row per series, origin and period, with the columns unique_id, ds, origin, step (1 to h),
    y (the real value), yhat and any quantile columns, and the attribute fit_seconds (the time spent in the
    forecaster, all origins together).
    """
    step = _periods(df)
    out, seconds = [], 0.0
    fitted = None
    for i, origin in enumerate(origins):
        train = df[df["ds"] <= origin]
        window = df[(df["ds"] > origin) & (df["ds"] <= origin + h * step)]
        future = window.drop(columns=["y"])
        # only series with history at this origin
        future = future[future["unique_id"].isin(train["unique_id"].unique())]
        start = time.perf_counter()
        if hasattr(forecaster, "fit"):
            if fitted is None or i % refit_every == 0:
                forecaster.fit(train)
                fitted = True
            fc = forecaster.predict(train, h, future)
        else:
            fc = forecaster(train, h, future)
        seconds += time.perf_counter() - start
        fc = fc.merge(window[["unique_id", "ds", "y"]], on=["unique_id", "ds"], how="inner")
        fc["origin"] = origin
        fc["step"] = ((fc["ds"] - origin) / step).round().astype(int)
        out.append(fc)
    result = pd.concat(out, ignore_index=True)
    result.attrs["fit_seconds"] = seconds
    return result


def scales(df, origins, season):
    """The MASE scale of each series at each origin: the mean absolute error of the seasonal-naive forecast
    (the value one season before) on the training data up to that origin."""
    rows = []
    for origin in origins:
        train = df[df["ds"] <= origin].sort_values(["unique_id", "ds"])
        diff = train.groupby("unique_id")["y"].diff(season).abs()
        s = diff.groupby(train["unique_id"]).mean()
        rows.append(pd.DataFrame({"unique_id": s.index, "origin": origin, "scale": s.to_numpy()}))
    return pd.concat(rows, ignore_index=True)


def quantile_columns(fc):
    return [c for c in fc.columns if c.startswith(QUANTILE_PREFIX) and c[1:].isdigit()]


def pinball(y, q, level):
    """Pinball loss of the quantile forecast q at the level (0 to 1): too-low forecasts cost `level` per
    unit, too-high forecasts cost 1 - level per unit."""
    diff = y - q
    return np.maximum(level * diff, (level - 1) * diff)


def stock_cost(prices, lost_sale=0.35, left_over=0.25):
    """The decision cost of a stock order: for every series and origin, the order is the forecast for the
    horizon added up. A unit short costs `lost_sale` of the price (the lost margin); a unit left over costs
    `left_over` of the price (sold at a 60% discount at the end of the season). `prices` maps unique_id to a
    price. Returns a function for score(cost=...)."""
    def cost(fc, column="yhat"):
        g = fc.groupby(["unique_id", "origin"]).agg(demand=("y", "sum"), order=(column, "sum")).reset_index()
        g["order"] = np.ceil(g["order"].clip(lower=0))
        p = g["unique_id"].map(prices).to_numpy()
        short = np.maximum(g["demand"] - g["order"], 0)
        over = np.maximum(g["order"] - g["demand"], 0)
        return float((short * lost_sale * p + over * left_over * p).sum() / g["origin"].nunique())
    return cost


def roster_cost(per_agent=6, agent_hour=28.0, short_hour=72.0, open_hours=range(7, 22)):
    """The decision cost of a help-desk roster: in every open hour, the roster has ceil(forecast / per_agent)
    agents and the hour needed ceil(tickets / per_agent). An extra agent hour costs `agent_hour` dollars; an
    hour short of one agent costs `short_hour` dollars (6 tickets that wait about a day longer). Returns a
    function for score(cost=...); the cost is per origin (one week of roster)."""
    def cost(fc, column="yhat"):
        f = fc[fc["ds"].dt.hour.isin(list(open_hours))]
        staff = np.ceil(f[column].clip(lower=0) / per_agent)
        need = np.ceil(f["y"] / per_agent)
        extra = np.maximum(staff - need, 0).sum()
        short = np.maximum(need - staff, 0).sum()
        return float((extra * agent_hour + short * short_hour) / f["origin"].nunique())
    return cost


def score(fc, df, method, season, horizon=None, cost=None, cost_column="yhat"):
    """One row of the backtest table.

    MASE: the mean, over series and origins, of the forecast's MAE divided by the series' scale (see
    scales()); series with a scale of 0 are left out. WAPE: all absolute errors added up, divided by all real
    values added up. bias: all forecasts minus all real values, divided by all real values (positive: too
    high). pinball: the mean pinball loss over the quantile columns, divided by the mean real value (empty
    without quantiles). fit s: the time in the forecaster. cost $: the decision cost per origin.
    """
    fc = fc.copy()
    if horizon is not None:
        fc = fc[fc["step"] <= horizon]
    err = fc["y"] - fc["yhat"]
    mae = err.abs().groupby([fc["unique_id"], fc["origin"]]).mean().rename("mae").reset_index()
    s = scales(df, sorted(fc["origin"].unique()), season)
    m = mae.merge(s, on=["unique_id", "origin"])
    m = m[m["scale"] > 0]
    total = fc["y"].sum()
    qs = quantile_columns(fc)
    if qs:
        loss = np.mean([pinball(fc["y"], fc[c], int(c[1:]) / 100).mean() for c in qs])
        pin = round(float(loss / fc["y"].mean()), 3)
    else:
        pin = None
    return {
        "method": method,
        "horizon": int(fc["step"].max()),
        "MASE": round(float((m["mae"] / m["scale"]).mean()), 3),
        "WAPE %": round(float(100 * err.abs().sum() / total), 1),
        "bias %": round(float(100 * (fc["yhat"] - fc["y"]).sum() / total), 1),
        "pinball": pin,
        "fit s": round(float(fc.attrs.get("fit_seconds", 0.0)), 2),
        "cost $": None if cost is None else round(cost(fc, cost_column)),
    }


def coverage(fc, low, high):
    """The share of real values inside the range [low, high] (two quantile column names)."""
    inside = (fc["y"] >= fc[low]) & (fc["y"] <= fc[high])
    return round(float(inside.mean()), 3)


def show(rows):
    """Print the backtest table, best MASE first."""
    table = pd.DataFrame(rows, columns=TABLE_COLUMNS).sort_values(["horizon", "MASE"])
    shown = table.astype(object).where(table.notna(), "")
    with pd.option_context("display.width", 120, "display.max_columns", 20):
        print(shown.to_string(index=False))
    return table


# Four simple forecasters (Module 3). Each one is a forecaster(train, h, future).

def naive(train, h, future):
    """The last value, for every period ahead."""
    last = train.sort_values("ds").groupby("unique_id")["y"].last()
    out = future[["unique_id", "ds"]].copy()
    out["yhat"] = out["unique_id"].map(last)
    return out


def seasonal_naive(season=7):
    """The value one season before (for daily data: the same weekday last week)."""
    def forecaster(train, h, future):
        t = train.sort_values("ds").groupby("unique_id").tail(season).copy()
        t["k"] = t.groupby("unique_id").cumcount()
        out = future[["unique_id", "ds"]].copy()
        out["k"] = out.groupby("unique_id").cumcount() % season
        out = out.merge(t[["unique_id", "k", "y"]], on=["unique_id", "k"], how="left")
        return out.rename(columns={"y": "yhat"}).drop(columns="k")
    forecaster.__name__ = f"seasonal_naive_{season}"
    return forecaster


def moving_average(window=28):
    """The mean of the last `window` periods, for every period ahead."""
    def forecaster(train, h, future):
        mean = train.sort_values("ds").groupby("unique_id")["y"].apply(lambda s: s.tail(window).mean())
        out = future[["unique_id", "ds"]].copy()
        out["yhat"] = out["unique_id"].map(mean)
        return out
    forecaster.__name__ = f"moving_average_{window}"
    return forecaster


def drift(train, h, future):
    """The last value plus the average change per period over the whole history."""
    t = train.sort_values("ds").groupby("unique_id")["y"]
    first, last, n = t.first(), t.last(), t.count()
    slope = (last - first) / (n - 1).clip(lower=1)
    out = future[["unique_id", "ds"]].copy()
    out["step"] = out.groupby("unique_id").cumcount() + 1
    out["yhat"] = out["unique_id"].map(last) + out["step"] * out["unique_id"].map(slope)
    return out.drop(columns="step")
