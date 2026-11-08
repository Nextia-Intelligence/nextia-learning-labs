"""The recommendation block's launch: daily orders and sales from September 2024 to early November 2025.

The block went live for everyone on Monday 6 October 2025. The same weeks had Thanksgiving (13 October) and an
autumn sale (9 to 19 October). This is the hook of Module 1 and the data of interrupted time series (Module 5).
"""

from datetime import date

import numpy as np
import pandas as pd
from scipy.stats import poisson

from ..world import HOLIDAYS, WEEKDAY, daterange, holiday_lift, season

NAME = "launch"
ABOUT = "Daily orders and sales around the recommendation block's launch (6 October 2025): no test, one series"
DEFAULT_SEED = 40
CUSTOMERS = None
START, DAYS = date(2024, 9, 2), 427  # to Sunday 2 November 2025
LAUNCH = date(2025, 10, 6)
SALE = (date(2025, 10, 9), date(2025, 10, 19))  # the autumn sale: 15% off garden furniture and decor
BLOCK = 1.02  # the true effect of the block on orders: +2%
SALE_ORDERS, SALE_BASKET = 1.11, 0.96


def run(seed, customers=None):
    rng = np.random.default_rng(seed)
    days = daterange(START, DAYS)
    t = np.arange(DAYS)
    base = 1450 * (1 + 0.00035 * t)  # slow growth
    shape = np.array([WEEKDAY[d.weekday()] * season(d) * holiday_lift(d) for d in days])
    sale = np.array([SALE[0] <= d <= SALE[1] for d in days])
    live = np.array([d >= LAUNCH for d in days])
    noise = rng.lognormal(0, 0.03, DAYS)
    expected0 = base * shape * np.where(sale, SALE_ORDERS, 1.0) * noise  # without the block
    expected1 = expected0 * np.where(live, BLOCK, 1.0)
    u = rng.random(DAYS)
    orders0, orders1 = poisson.ppf(u, expected0), poisson.ppf(u, expected1)  # the same random numbers
    basket = 84 * rng.lognormal(0, 0.015, DAYS) * np.where(sale, SALE_BASKET, 1.0)
    df = pd.DataFrame({
        "date": [d.isoformat() for d in days], "weekday": [d.strftime("%a") for d in days],
        "orders": orders1.astype(int), "sales": np.round(orders1 * basket, 2),
        "holiday": [HOLIDAYS.get(d, "") for d in days],
        "holiday_window": [int(holiday_lift(d) != 1.0) for d in days],  # the shopping days around a holiday
        "sale": sale.astype(int), "block_live": live.astype(int),
    })
    counterfactual = pd.DataFrame({"date": df["date"], "orders_without_block": orders0.astype(int),
                                   "sales_without_block": np.round(orders0 * basket, 2)})
    after = (df.date >= "2025-10-06") & (df.date <= "2025-11-02")
    before = (df.date >= "2025-09-08") & (df.date <= "2025-10-05")
    s_after, s_before = df.sales[after].sum(), df.sales[before].sum()
    cf_after = counterfactual.sales_without_block[after].sum()
    truth = {
        "launch": LAUNCH.isoformat(), "block_effect_on_orders": round(BLOCK - 1, 4),
        "naive_before_after": {"before": "2025-09-08 to 2025-10-05", "after": "2025-10-06 to 2025-11-02",
                               "sales_before": round(float(s_before), 2), "sales_after": round(float(s_after), 2),
                               "change": round(float(s_after / s_before - 1), 4)},
        "sales_after_without_block": round(float(cf_after), 2),
        "true_effect_after": {"sales": round(float(s_after - cf_after), 2),
                              "relative": round(float(s_after / cf_after - 1), 4),
                              "orders": int(orders1[after].sum() - orders0[after].sum())},
    }
    meta = {"about": ABOUT, "unit": "day", "start": START.isoformat(), "end": days[-1].isoformat(),
            "events": {"launch": LAUNCH.isoformat(), "thanksgiving": "2025-10-13",
                       "sale": f"{SALE[0].isoformat()} to {SALE[1].isoformat()}"},
            "note": "counterfactual.csv is the simulator's truth: the same days without the block."}
    return {"daily": df, "counterfactual": counterfactual}, truth, meta
