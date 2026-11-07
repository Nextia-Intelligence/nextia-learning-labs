"""Forecast every product in every region for the next 14 days, and the help-desk tickets for the next week.

The methods are the ones that the course chose from its backtest table: exponential smoothing with a weekly
season (ETS, additive error and season) for the products, with the promotion uplift of each category on the
planned promotion days, and MSTL with a daily and a weekly season for the tickets. Both give a range (80%
and 90%), not only one number.
"""

import os

import numpy as np
import pandas as pd

from . import config

os.environ.setdefault("NIXTLA_ID_AS_COL", "1")

MIN_HISTORY_DAYS = 28  # a newer product gets the mean of its last 7 days instead of ETS


def clean_series(demand):
    """One column per product and region, one row per day. Days with no row (a missing feed day) and
    stock-out days (sales lower than demand) are filled with the mean of the same weekday one and two weeks
    before, so that the model does not learn a stock-out as low demand."""
    d = demand.assign(unique_id=demand["product_id"] + "/" + demand["region"])
    y = d["sales"].astype(float).where(d["stock_out"] == 0)
    wide = pd.DataFrame({"unique_id": d["unique_id"], "ds": d["date"], "y": y}).pivot(
        index="ds", columns="unique_id", values="y")
    wide = wide.reindex(pd.date_range(wide.index.min(), wide.index.max(), freq="D"))
    first = d.groupby("unique_id")["date"].min()
    before_start = wide.index.to_numpy()[:, None] < first.reindex(wide.columns).to_numpy()[None, :]
    for _ in range(3):  # a stock-out of more than a week needs more than one pass
        w7, w14 = wide.shift(7), wide.shift(14)
        wide = wide.fillna(((w7 + w14) / 2).fillna(w7).fillna(w14))
    wide = wide.fillna(wide.shift(-7)).fillna(0.0)
    wide = wide.mask(before_start)
    long = wide.rename_axis("ds").reset_index().melt(id_vars="ds", var_name="unique_id", value_name="y")
    return long.dropna(subset=["y"]).sort_values(["unique_id", "ds"]).reset_index(drop=True)


def promotion_uplift(demand, products, last_weeks=52):
    """The mean sales on promotion days divided by the mean on other days, per category (last 52 weeks)."""
    end = demand["date"].max()
    d = demand[demand["date"] > end - pd.Timedelta(weeks=last_weeks)].merge(products[["product_id", "category"]])
    m = d.groupby(["category", "product_id", "on_promotion"])["sales"].mean().unstack()
    if 1 not in m.columns:
        return {}
    ratio = (m[1] / m[0]).replace([np.inf, -np.inf], np.nan).dropna()
    return ratio.groupby(level=0).median().clip(1.0, 3.0).round(2).to_dict()


def forecast_products(inputs):
    """The forecast of every product and region for the 14 days from the Monday: unique_id, product_id,
    region, ds, yhat, and the range q5, q10, q90, q95."""
    from statsforecast import StatsForecast
    from statsforecast.models import AutoETS

    h = config.HORIZON_DAYS
    long = clean_series(inputs.demand)
    size = long.groupby("unique_id")["y"].size()
    old = size[size >= MIN_HISTORY_DAYS].index
    sf = StatsForecast(models=[AutoETS(season_length=config.SEASON_DAYS, model="ANA")], freq="D", n_jobs=1)
    fc = sf.forecast(df=long[long["unique_id"].isin(old)], h=h, level=config.LEVELS)
    out = pd.DataFrame({"unique_id": fc["unique_id"], "ds": fc["ds"], "yhat": fc["AutoETS"]})
    for lv in config.LEVELS:
        lo = (100 - lv) // 2
        out[f"q{lo}"] = fc[f"AutoETS-lo-{lv}"].to_numpy()
        out[f"q{100 - lo}"] = fc[f"AutoETS-hi-{lv}"].to_numpy()
    days = pd.date_range(inputs.week, periods=h, freq="D")
    young = []
    for uid in size.index.difference(old):
        mean = float(long[long["unique_id"] == uid]["y"].tail(7).mean())
        sd = max(np.sqrt(mean), 0.5)  # a count's typical spread when there is too little history
        young.append(pd.DataFrame({"unique_id": uid, "ds": days, "yhat": mean, "q5": mean - 1.645 * sd,
                                   "q10": mean - 1.282 * sd, "q90": mean + 1.282 * sd, "q95": mean + 1.645 * sd}))
    out = pd.concat([out, *young], ignore_index=True)
    out[["product_id", "region"]] = out["unique_id"].str.split("/", expand=True)
    # planned promotions: the category's usual uplift on the promotion days
    uplift = promotion_uplift(inputs.demand, inputs.products)
    cat = dict(zip(inputs.products["product_id"], inputs.products["category"], strict=True))
    promo = inputs.promotions
    out["on_promotion"] = 0
    for p in promo[(promo["end"] >= days[0]) & (promo["start"] <= days[-1])].itertuples():
        m = (out["product_id"] == p.product_id) & (out["ds"] >= p.start) & (out["ds"] <= p.end)
        out.loc[m, "on_promotion"] = 1
        out.loc[m, ["yhat", "q5", "q10", "q90", "q95"]] *= uplift.get(cat[p.product_id], 1.0)
    cols = ["yhat", "q5", "q10", "q90", "q95"]
    out[cols] = out[cols].clip(lower=0).round(3)
    return out[["unique_id", "product_id", "region", "ds", "on_promotion", *cols]].sort_values(
        ["unique_id", "ds"]).reset_index(drop=True)


def reconcile(fc, products):
    """Bottom-up: every total is the sum of its products, so the plan adds up at every level."""
    f = fc.merge(products[["product_id", "category"]], on="product_id")
    rows = [f.groupby("ds", as_index=False)["yhat"].sum().assign(level="total", key="total")]
    levels = [("region", ["region"]), ("category", ["category"]), ("region/category", ["region", "category"])]
    for level, keys in levels:
        g = f.groupby(keys + ["ds"], as_index=False)["yhat"].sum()
        g["key"] = g[keys].astype(str).agg("/".join, axis=1)
        rows.append(g.assign(level=level)[["ds", "yhat", "level", "key"]])
    out = pd.concat(rows, ignore_index=True)[["level", "key", "ds", "yhat"]]
    out["yhat"] = out["yhat"].round(2)
    return out.sort_values(["level", "key", "ds"]).reset_index(drop=True)


def forecast_tickets(inputs):
    """All help-desk tickets per hour for the next week (MSTL, seasons of 24 and 168 hours, last 12 weeks)."""
    from statsforecast import StatsForecast
    from statsforecast.models import MSTL, AutoETS

    t = inputs.tickets.groupby("timestamp", as_index=False)["tickets"].sum().tail(config.TICKET_HISTORY_HOURS)
    df = pd.DataFrame({"unique_id": "tickets", "ds": t["timestamp"], "y": t["tickets"].astype(float)})
    model = MSTL(season_length=[24, 168], trend_forecaster=AutoETS(model="ZZN"))
    fc = StatsForecast(models=[model], freq="h", n_jobs=1).forecast(df=df, h=config.TICKET_HORIZON_HOURS, level=[80])
    out = pd.DataFrame({"ds": fc["ds"], "yhat": fc["MSTL"], "q10": fc["MSTL-lo-80"], "q90": fc["MSTL-hi-80"]})
    return out.assign(**{c: out[c].clip(lower=0).round(3) for c in ["yhat", "q10", "q90"]})
