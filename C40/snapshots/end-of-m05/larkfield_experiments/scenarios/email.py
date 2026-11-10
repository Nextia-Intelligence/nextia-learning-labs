"""The reminder email (Rafael's test). Randomised by customer; the outcome is an order in the 14 days after
the email. The email helps some customers and annoys others (Module 7)."""

import numpy as np
import pandas as pd

from ..world import PROVINCE_SHARE, PROVINCES

NAME = "email"
ABOUT = "A reminder email to customers who have not ordered for 30 days: an A/B test by customer, 14 days"
DEFAULT_SEED = 40
CUSTOMERS = 60_000
TARGETS = 50_000  # next month's list: the customers Rafael must choose from in Module 7


def _customers(rng, n, start_id):
    new = rng.random(n) < 0.25
    tenure = np.where(new, rng.integers(35, 180, n), rng.integers(180, 2500, n))
    orders_12m = np.where(new, rng.integers(1, 3, n), rng.negative_binomial(1.6, 0.32, n) + 1)
    days_since = rng.integers(30, 240, n)
    opens = np.clip(rng.beta(1.3, 3.0, n), 0, 1)
    spend = np.round(orders_12m * 80 * rng.lognormal(0, 0.35, n), 2)
    return pd.DataFrame({
        "customer_id": [f"E{i:06d}" for i in range(start_id, start_id + n)],
        "province": rng.choice(PROVINCES, size=n, p=PROVINCE_SHARE),
        "device": np.where(rng.random(n) < 0.58, "mobile", "desktop"),
        "new_customer": new.astype(int), "tenure_days": tenure, "orders_12m": orders_12m,
        "spend_12m": spend, "days_since_order": days_since, "email_open_rate": np.round(opens, 3),
    })


def chances(df, rng):
    """The chance to order in 14 days without the email (p0) and with it (p1). This is the simulator's secret."""
    z = (-2.55 + 0.45 * np.log1p(df.orders_12m) - 0.006 * (df.days_since_order - 30)
         + 0.6 * df.email_open_rate - 0.15 * (df.device == "mobile"))
    noise = rng.normal(0, 0.35, len(df))
    tau = (0.75 * ((df.tenure_days < 365) & (df.orders_12m <= 3)) + 0.9 * df.email_open_rate
           - 0.9 * (df.orders_12m >= 7) - 0.25)
    tau = tau + rng.normal(0, 0.15, len(df))
    p0 = 1 / (1 + np.exp(-(z + noise)))
    p1 = 1 / (1 + np.exp(-(z + noise + tau)))
    unsub0 = np.full(len(df), 0.002)
    unsub1 = 0.004 + 0.03 * (df.orders_12m >= 7).to_numpy()
    return p0.to_numpy(), p1.to_numpy(), unsub0, unsub1


def run(seed, customers=None):
    rng = np.random.default_rng(seed)
    n = customers or CUSTOMERS
    df = _customers(rng, n, 1)
    p0, p1, s0, s1 = chances(df, rng)
    variant = rng.random(n) < 0.5
    u, v, value = rng.random(n), rng.random(n), np.round(85 * rng.lognormal(-0.1, 0.5, n), 2)
    y0, y1 = u < p0, u < p1  # both worlds, with the same random numbers
    un0, un1 = v < s0, v < s1
    df.insert(1, "variant", np.where(variant, "B", "A"))
    df["ordered"] = np.where(variant, y1, y0).astype(int)
    df["revenue"] = np.where(df["ordered"] == 1, value, 0.0)
    df["unsubscribed"] = np.where(variant, un1, un0).astype(int)
    groups = {"persuadable": int((~y0 & y1).sum()), "sure_thing": int((y0 & y1).sum()),
              "lost_cause": int((~y0 & ~y1).sum()), "do_not_disturb": int((y0 & ~y1).sum())}
    targets = _customers(rng, TARGETS, 500_001)
    t0, t1, _, _ = chances(targets, rng)
    truth = {
        "customers": n,
        "ordered": {"control_world": round(float(y0.mean()), 5), "treated_world": round(float(y1.mean()), 5),
                    "effect": round(float(y1.mean() - y0.mean()), 5),
                    "relative": round(float((y1.mean() - y0.mean()) / y0.mean()), 4),
                    "expected_effect": round(float((p1 - p0).mean()), 5), "unit": "share of customers with an order"},
        "revenue": {"control_world": round(float((value * y0).mean()), 4),
                    "treated_world": round(float((value * y1).mean()), 4),
                    "effect": round(float((value * (y1.astype(int) - y0)).mean()), 4), "unit": "dollars per customer"},
        "unsubscribed": {"control_world": round(float(un0.mean()), 5), "treated_world": round(float(un1.mean()), 5),
                         "effect": round(float(un1.mean() - un0.mean()), 5), "unit": "share of customers"},
        "groups": groups,
        "targets": {"customers": TARGETS, "expected_extra_orders_all": round(float((t1 - t0).sum()), 1),
                    "best_10000": round(float(np.sort(t1 - t0)[-10_000:].sum()), 1),
                    "harmed": int(((t1 - t0) < 0).sum())},
    }
    target_truth = pd.DataFrame({"customer_id": targets.customer_id, "true_uplift": np.round(t1 - t0, 5)})
    meta = {"about": ABOUT, "unit": "customer", "days": 14, "start": "2025-09-15", "end": "2025-09-28",
            "variants": {"A": "no email", "B": "the reminder email"}, "primary_metric": "ordered", "split": 0.5,
            "guardrails": ["unsubscribed"],
            "note": "targets.csv is next month's list (no outcomes); truth_targets.csv is the simulator's truth."}
    tables = {"customers": df, "targets": targets, "truth_targets": target_truth}
    return tables, truth, meta
