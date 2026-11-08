"""A "popular now" badge on the 40 best-selling products, tested by customer, when stock is short
(a practice problem we made on purpose).

The badge makes B customers buy the best sellers sooner. Each best seller has a fixed stock each day, so when B
customers buy it, A customers find it sold out later that day. A loses orders because of B: the groups affect
each other (interference), and the test shows a bigger difference than a launch to everyone would give.
"""

import numpy as np
import pandas as pd

from ..world import TEST_START, WEEKDAY, daterange, holiday_lift, make_population, season

NAME = "stock"
ABOUT = "A 'popular now' badge on best sellers with short stock, tested by customer (planted interference)"
DEFAULT_SEED = 40
CUSTOMERS = 150_000
PRODUCTS, BEST = 400, 40
LIFT = 0.30  # the badge raises the chance to order a best seller by 30%


def simulate(seed, n, design):
    """design: 'customer' (a coin flip per customer) or 'switchback' (a coin flip per day, for everyone)."""
    rng = np.random.default_rng(seed)
    pop = make_population(n, rng)
    by_customer = rng.random(n) < 0.5
    popularity = 1 / np.arange(1, PRODUCTS + 1) ** 0.9
    popularity /= popularity.sum()
    days = daterange(TEST_START, 28)
    pairs = rng.random(14) < 0.5  # switchback: in each pair of days, one is A and one is B, by a coin flip
    day_b = np.array([pairs[i // 2] == (i % 2 == 0) for i in range(28)])
    exp_orders = None
    visits, totals = [], {w: np.zeros(n) for w in ("A", "B", "test")}
    seen = np.zeros(n, bool)
    for k, d in enumerate(days):
        p = np.minimum(pop.visit_rate * WEEKDAY[d.weekday()] * season(d) * holiday_lift(d), 0.9)
        idx = rng.permutation(np.nonzero(rng.random(n) < p)[0])  # visits in the order they arrive
        seen[idx] = True
        product = rng.choice(PRODUCTS, size=len(idx), p=popularity)
        best = product < BEST
        u, value = rng.random(len(idx)), pop.basket[idx] * rng.lognormal(-0.1, 0.45, len(idx))
        if exp_orders is None:  # the day's stock of each best seller: about what A customers would buy
            exp_orders = np.bincount(product[best], weights=pop.conv[idx][best], minlength=PRODUCTS)[:BEST]
        stock0 = np.floor(exp_orders * WEEKDAY[d.weekday()] + 0.5).astype(int)
        b_test = by_customer[idx] if design == "customer" else np.full(len(idx), day_b[k])
        out = {}
        for world, treated in (("A", np.zeros(len(idx), bool)), ("B", np.ones(len(idx), bool)), ("test", b_test)):
            stock = stock0.copy()
            pr = pop.conv[idx] * np.where(treated & best, 1 + LIFT, 1.0)
            want = u < pr
            got = want.copy()
            for j in np.nonzero(want & best)[0]:
                if stock[product[j]] > 0:
                    stock[product[j]] -= 1
                else:
                    got[j] = False  # sold out
            out[world] = got
            np.add.at(totals[world], idx, value * got)
        visits.append(pd.DataFrame({"date": d.isoformat(), "customer_id": pop.customer_id[idx],
                                    "variant": np.where(b_test, "B", "A"), "product": product + 1,
                                    "best_seller": best.astype(int), "ordered": out["test"].astype(int),
                                    "revenue": np.round(value * out["test"], 2),
                                    "sold_out": (u < pop.conv[idx] * np.where(b_test & best, 1 + LIFT, 1.0))
                                    .astype(int) - out["test"].astype(int)}))
    v = pd.concat(visits, ignore_index=True)
    launch = float((totals["B"][seen] - totals["A"][seen]).mean())
    truth = {"revenue": {"effect": round(launch, 4), "unit": "dollars per customer, badge for everyone against nobody",
                         "relative": round(launch / float(totals["A"][seen].mean()), 4)},
             "planted": "Shared stock: B customers buy best sellers that A customers would have bought."}
    return v, truth, day_b


def run(seed, customers=None):
    v, truth, _ = simulate(seed, customers or CUSTOMERS, "customer")
    per = v.groupby("customer_id").agg(variant=("variant", "first"), visits=("date", "size"), orders=("ordered", "sum"),
                                       revenue=("revenue", "sum"), sold_out=("sold_out", "sum")).reset_index()
    meta = {"about": ABOUT, "unit": "customer", "days": 28, "start": "2025-09-08", "end": "2025-10-05",
            "variants": {"A": "no badge", "B": "the 'popular now' badge"}, "primary_metric": "revenue", "split": 0.5}
    return {"customers": per, "visits": v}, truth, meta
