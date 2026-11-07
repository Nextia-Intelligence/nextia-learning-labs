"""Turn the forecast ranges into decisions: the stock order for 14 days and the help-desk roster for a week.

The newsvendor idea: order the quantile of demand that matches the costs. If a lost sale costs 0.35 of the
price and a left-over item 0.25, you want enough stock 0.35 / (0.35 + 0.25) = 58% of the time.
"""

import numpy as np
from scipy.stats import norm

from . import config

Z80 = norm.ppf(0.9)  # the 80% range is the mean plus or minus 1.28 standard deviations


def _expected_short_over(order, mean, sd):
    """For a normal demand: the expected units short and the expected units left over."""
    sd = np.maximum(sd, 1e-9)
    z = (order - mean) / sd
    short = sd * (norm.pdf(z) - z * (1 - norm.cdf(z)))
    over = (order - mean) + short
    return short, over


def stock_orders(fc, products, quantile=config.STOCK_QUANTILE):
    """One order per product and region for the 14 days: the forecast added up, its 80% range (the days
    taken as independent), the order at the cost quantile, and its expected cost."""
    g = fc.assign(sd=(fc["q90"] - fc["q10"]) / (2 * Z80)).groupby(["product_id", "region"]).agg(
        forecast=("yhat", "sum"), var=("sd", lambda s: float((s ** 2).sum())))
    g["sd"] = np.sqrt(g.pop("var"))
    g = g.reset_index().merge(products[["product_id", "name", "category", "base_price"]], on="product_id")
    g["low_80"] = np.maximum(g["forecast"] - Z80 * g["sd"], 0)
    g["high_80"] = g["forecast"] + Z80 * g["sd"]
    g["order"] = np.ceil(np.maximum(g["forecast"] + norm.ppf(quantile) * g["sd"], 0)).astype(int)
    short, over = _expected_short_over(g["order"], g["forecast"], g["sd"])
    g["expected_cost"] = (short * config.LOST_SALE_SHARE + over * config.LEFT_OVER_SHARE) * g["base_price"]
    g["stock_out_chance"] = 1 - norm.cdf((g["order"] - g["forecast"]) / np.maximum(g["sd"], 1e-9))
    cols = ["forecast", "sd", "low_80", "high_80", "expected_cost", "stock_out_chance"]
    g[cols] = g[cols].round(2)
    return g[["product_id", "region", "name", "category", "base_price", "forecast", "low_80", "high_80", "sd",
              "order", "expected_cost", "stock_out_chance"]].sort_values(
                  ["product_id", "region"]).reset_index(drop=True)


def roster(tickets_fc, quantile=config.ROSTER_QUANTILE):
    """Agents per hour for the week: enough for the cost quantile of the tickets, at least one agent in
    every open hour, none outside the open hours."""
    t = tickets_fc.copy()
    sd = np.maximum((t["q90"] - t["q10"]) / (2 * Z80), 1e-9)
    t["plan_tickets"] = np.maximum(t["yhat"] + norm.ppf(quantile) * sd, 0)
    open_ = t["ds"].dt.hour.isin(list(config.OPEN_HOURS))
    t["agents"] = np.where(open_, np.maximum(np.ceil(t["plan_tickets"] / config.TICKETS_PER_AGENT_HOUR), 1), 0)
    t["agents"] = t["agents"].astype(int)
    # expected cost per open hour, with the tickets in agent units (6 tickets = one agent hour)
    short, over = _expected_short_over(t["agents"], t["yhat"] / config.TICKETS_PER_AGENT_HOUR,
                                       sd / config.TICKETS_PER_AGENT_HOUR)
    t["expected_cost"] = np.where(open_, short * config.SHORT_HOUR_USD + over * config.AGENT_HOUR_USD, 0.0)
    t[["plan_tickets", "expected_cost"]] = t[["plan_tickets", "expected_cost"]].round(2)
    return t.rename(columns={"ds": "hour", "yhat": "tickets"})[
        ["hour", "tickets", "q10", "q90", "plan_tickets", "agents", "expected_cost"]]


def summary(orders, rost):
    return {
        "order_units": int(orders["order"].sum()),
        "order_value_usd": round(float((orders["order"] * orders["base_price"]).sum())),
        "order_expected_cost_usd": round(float(orders["expected_cost"].sum())),
        "agent_hours": int(rost["agents"].sum()),
        "roster_expected_cost_usd": round(float(rost["expected_cost"].sum())),
        "peak_hour": str(rost.loc[rost["tickets"].idxmax(), "hour"]),
        "peak_agents": int(rost["agents"].max()),
    }


def write(out_dir, fc, totals, orders, rost):
    out_dir.mkdir(parents=True, exist_ok=True)
    fc.assign(ds=fc["ds"].dt.strftime("%Y-%m-%d")).to_csv(out_dir / "forecast.csv", index=False)
    totals.assign(ds=totals["ds"].dt.strftime("%Y-%m-%d")).to_csv(out_dir / "totals.csv", index=False)
    orders.to_csv(out_dir / "orders.csv", index=False)
    rost.assign(hour=rost["hour"].dt.strftime("%Y-%m-%d %H:%M")).to_csv(out_dir / "roster.csv", index=False)
