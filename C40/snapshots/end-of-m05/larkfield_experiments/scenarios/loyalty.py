"""The Gold loyalty tier: customers who spent 500 dollars or more in 2024 became Gold on 1 January 2025 (free
returns and 5% back in points). Customers did not choose the threshold, so the customers just above and just
below 500 are alike, except for the tier: a regression discontinuity.

A practice problem we made on purpose: some customers who were close to 500 in December added a small order to
reach Gold. They are bargain hunters who spend less later, and they all sit just above the line.
"""

import numpy as np
import pandas as pd

NAME = "loyalty"
ABOUT = "The Gold tier from 500 dollars of 2024 spending: spending in the first half of 2025 (no test)"
DEFAULT_SEED = 40
CUSTOMERS = 50_000
THRESHOLD, TIER_EFFECT = 500.0, 45.0  # Gold adds 45 dollars of spending in six months at the threshold


def run(seed, customers=None):
    rng = np.random.default_rng(seed)
    n = customers or CUSTOMERS
    spend = np.round(rng.lognormal(np.log(330), 0.65, n), 2)  # the running variable: 2024 spending
    tenure = rng.integers(200, 2500, n)
    near = (spend >= 455) & (spend < THRESHOLD)
    gamer = near & (rng.random(n) < 0.45)
    spend = np.where(gamer, np.round(THRESHOLD + rng.uniform(1, 35, n), 2), spend)  # the extra December order
    base = 18 + 0.42 * spend - 0.00011 * spend**2 + 0.004 * tenure
    y0 = np.maximum(base * rng.lognormal(-0.02, 0.2, n) - 60 * gamer, 0)
    gold = spend >= THRESHOLD
    tau = TIER_EFFECT + 0.03 * (spend - THRESHOLD)
    y1 = y0 + tau
    y = np.where(gold, y1, y0)
    df = pd.DataFrame({"customer_id": [f"L{i:06d}" for i in range(1, n + 1)], "spend_2024": spend,
                       "tenure_days": tenure, "gold": gold.astype(int), "spend_2025_h1": np.round(y, 2)})
    truth = {"threshold": THRESHOLD,
             "effect": {"at_threshold": TIER_EFFECT, "unit": "dollars of spending in six months, at 500 dollars"},
             "naive": {"gold": round(float(y[gold].mean()), 2), "not_gold": round(float(y[~gold].mean()), 2)},
             "gamers": int(gamer.sum()),
             "planted": "Bargain hunters near 500 added a small order to reach Gold; they spend 60 dollars less "
                        "later and sit between 500 and 535."}
    meta = {"about": ABOUT, "unit": "customer", "running_variable": "spend_2024", "threshold": THRESHOLD,
            "outcome": "spend_2025_h1"}
    return {"customers": df}, truth, meta
