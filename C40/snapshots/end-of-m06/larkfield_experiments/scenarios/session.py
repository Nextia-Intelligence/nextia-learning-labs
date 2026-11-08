"""The recommendation block, randomised by session instead of by customer (a practice problem we made on purpose).

Each visit (session) gets A or B by its own coin flip, so most customers see both versions. The block helps in
the session where it is shown, and it also helps later: a customer who has seen it once comes back to the
products it showed. That later help reaches the A sessions too, so A against B by session misses part of the
effect that a launch to everyone would have.
"""

import numpy as np
import pandas as pd

from ..world import TEST_START, WEEKDAY, daterange, holiday_lift, make_population, season

NAME = "session"
ABOUT = "The recommendation block randomised by session: customers see both versions (planted)"
DEFAULT_SEED = 40
CUSTOMERS = 200_000
NOW, LATER = 0.03, 0.08  # +3% on the chance to order in a B session; +8% in every session after a first B


def run(seed, customers=None):
    rng = np.random.default_rng(seed)
    n = customers or CUSTOMERS
    pop = make_population(n, rng)
    seen_mix, seen_all_b = np.zeros(n, bool), np.zeros(n, bool)
    rows, tot = [], {k: np.zeros(n) for k in ("visits", "r0", "r1")}
    sid = 0
    for d in daterange(TEST_START, 28):
        p = np.minimum(pop.visit_rate * WEEKDAY[d.weekday()] * season(d) * holiday_lift(d), 0.9)
        idx = np.nonzero(rng.random(n) < p)[0]
        b = rng.random(len(idx)) < 0.5  # the coin flip per session
        u, value = rng.random(len(idx)), pop.basket[idx] * rng.lognormal(-0.1, 0.45, len(idx))
        p0 = pop.conv[idx]
        p_mix = p0 * (1 + NOW * b) * (1 + LATER * seen_mix[idx])
        p_all_b = p0 * (1 + NOW) * (1 + LATER * seen_all_b[idx])
        r_mix, r0, r1 = value * (u < p_mix), value * (u < p0), value * (u < p_all_b)
        seen_mix[idx[b]] = True
        seen_all_b[idx] = True
        np.add.at(tot["visits"], idx, 1)
        np.add.at(tot["r0"], idx, r0)
        np.add.at(tot["r1"], idx, r1)
        rows.append(pd.DataFrame({"date": d.isoformat(), "session_id": np.arange(sid, sid + len(idx)) + 1,
                                  "customer_id": pop.customer_id[idx], "variant": np.where(b, "B", "A"),
                                  "ordered": (u < p_mix).astype(int), "revenue": np.round(r_mix, 2),
                                  "_r0": r0, "_r1": r1}))
        sid += len(idx)
    visits = pd.concat(rows, ignore_index=True)
    seen = tot["visits"] > 0
    per = visits.groupby("customer_id").agg(sessions=("session_id", "size"),
                                            versions=("variant", lambda s: "both" if s.nunique() > 1 else s.iloc[0]),
                                            revenue=("revenue", "sum")).reset_index()
    truth = {
        "revenue": {"effect": round(float(visits._r1.mean() - visits._r0.mean()), 4),
                        "relative": round(float(visits._r1.mean() / visits._r0.mean() - 1), 4),
                        "unit": "dollars per session, if everyone got the block"},
        "revenue_per_customer": {"effect": round(float((tot["r1"][seen] - tot["r0"][seen]).mean()), 4),
                    "unit": "dollars per customer, if everyone got the block"},
        "customers_who_saw_both": round(float((per.versions == "both").mean()), 4),
        "planted": "Randomised by session: the block's later effect reaches A sessions too.",
    }
    visits = visits.drop(columns=["_r0", "_r1"])
    meta = {"about": ABOUT, "unit": "session", "days": 28, "start": "2025-09-08", "end": "2025-10-05",
            "variants": {"A": "no block", "B": "the recommendation block"}, "primary_metric": "revenue",
            "analysis_table": "visits"}
    return {"visits": visits, "customers": per}, truth, meta
