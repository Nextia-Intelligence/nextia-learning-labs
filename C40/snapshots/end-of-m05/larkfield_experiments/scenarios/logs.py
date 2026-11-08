"""Logs after the recommendation block went live for everyone: who clicked it, and what they spent.

No test: customers chose to use the block. The customers who use it were already more active, so "users spent
more" mixes the block's effect with who the users are. A practice problem we made on purpose (self-selection).
One cause is hidden on purpose: whether the customer has a garden. It is not in the log (Module 6).
"""

import numpy as np
from scipy.stats import binom

from ..world import make_population

NAME = "logs"
ABOUT = "28 days of logs after the recommendation block's launch: who used it and what they spent (no test)"
DEFAULT_SEED = 40
CUSTOMERS = 40_000
LIFT = 0.07  # using the block raises a customer's chance to order on each visit by 7% (synthetic)


def run(seed, customers=None):
    rng = np.random.default_rng(seed)
    n = customers or CUSTOMERS
    pop = make_population(n, rng, visits_per_week=0.7)
    garden = rng.random(n) < 0.45  # hidden: never written to the log
    visits = rng.poisson(pop.visit_rate * 28) + 1  # everyone in the log visited at least once
    z = lambda x: (x - x.mean()) / x.std()  # noqa: E731
    logit = (-1.0 + 0.07 * z(np.log(visits)) + 0.06 * z(np.log1p(pop.pre_spend)) + 0.3 * (pop.device == "desktop")
             + 0.35 * garden + 0.15 * z(np.log1p(pop.tenure_days)))
    used = rng.random(n) < 1 / (1 + np.exp(-logit))
    conv = np.minimum(pop.conv * np.where(garden, 1.25, 1.0), 0.9)
    u = rng.random(n)
    orders0 = binom.ppf(u, visits, conv)
    orders1 = binom.ppf(u, visits, np.minimum(conv * (1 + LIFT), 0.95))
    value = pop.basket * rng.lognormal(-0.1, 0.3, n) * np.where(garden, 1.15, 1.0)
    spend0, spend1 = orders0 * value, orders1 * value
    spend = np.where(used, spend1, spend0)
    intent = rng.normal(0, 1, n)
    pages = rng.poisson(visits * 4 * np.exp(0.25 * intent)) + used * rng.poisson(5, n)  # a mediator
    review = rng.random(n) < 1 / (1 + np.exp(-(-3.2 + 0.9 * used + 0.012 * spend)))  # a collider
    df = pop.table()
    df["visits"] = visits
    df["pages_viewed"] = pages
    df["used_block"] = used.astype(int)
    df["orders"] = np.where(used, orders1, orders0).astype(int)
    df["revenue"] = np.round(spend, 2)
    df["left_review"] = review.astype(int)
    eff = spend1 - spend0
    naive = df.revenue[used].mean() / df.revenue[~used].mean() - 1
    truth = {
        "customers": n, "used_block": int(used.sum()),
        "naive": {"users": round(float(df.revenue[used].mean()), 2), "non_users": round(float(df.revenue[~used].mean()), 2),
                  "difference": round(float(df.revenue[used].mean() - df.revenue[~used].mean()), 2),
                  "relative": round(float(naive), 4)},
        "ate": {"effect": round(float(eff.mean()), 4), "unit": "dollars per customer, if everyone used the block"},
        "att": {"effect": round(float(eff[used].mean()), 4), "unit": "dollars per customer, among the users"},
        "hidden_confounder_size": {"share_gap": round(float(garden[used].mean() - garden[~used].mean()), 4),
                                   "dollars": round(float(spend0[garden].mean() - spend0[~garden].mean()), 2)},
        "hidden_confounder": "has_garden (45% of customers): users are more likely to have a garden, and gardeners "
                             "spend more. It is not in the log.",
    }
    meta = {"about": ABOUT, "unit": "customer", "days": 28, "start": "2025-10-06", "end": "2025-11-02",
            "treatment": "used_block (clicked a product in the block at least once)", "outcome": "revenue",
            "columns": {"pages_viewed": "pages seen in the 28 days (the block adds pages: a mediator)",
                        "left_review": "wrote a product review (caused by both the block and spending: a collider)",
                        "pre_spend": "spending in the 8 weeks before the launch"}}
    return {"customers": df}, truth, meta
