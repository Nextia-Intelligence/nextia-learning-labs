"""The "popular now" badge with short stock, tested by day instead of by customer: a switchback test.

Every customer gets the same version on the same day, and the version switches between days (a coin flip in
each pair of days). A and B never share a day's stock, so they cannot take orders from each other. The cost:
only 28 units (days), so the interval is wide.
"""

from .stock import CUSTOMERS, simulate

NAME = "switchback"
ABOUT = "The 'popular now' badge with short stock, switched by day for everyone (a switchback test)"
DEFAULT_SEED = 40


def run(seed, customers=None):
    v, truth, day_b = simulate(seed, customers or CUSTOMERS, "switchback")
    days = v.groupby("date").agg(variant=("variant", "first"), visits=("customer_id", "size"),
                                 orders=("ordered", "sum"), revenue=("revenue", "sum")).reset_index()
    days["revenue_per_visit"] = (days["revenue"] / days["visits"]).round(4)
    per_visit = truth["revenue"]["effect"]  # per customer; add the per-visit truth for the day-level analysis
    truth["revenue_per_visit"] = {"effect": round(float(per_visit * v.customer_id.nunique() / len(v)), 4),
                                  "unit": "dollars per visit, badge for everyone against nobody (approximate)"}
    meta = {"about": ABOUT, "unit": "day", "days": 28, "start": "2025-09-08", "end": "2025-10-05",
            "variants": {"A": "no badge", "B": "the 'popular now' badge"}, "primary_metric": "revenue_per_visit",
            "analysis_table": "days"}
    return {"days": days, "visits": v}, truth, meta
