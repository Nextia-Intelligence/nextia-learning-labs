"""A new product page layout, checked on 20 metrics (a practice problem we made on purpose).

The layout changes nothing: every true effect is zero. With 20 metrics and the 5% rule, about one metric "wins"
by chance. With this seed, exactly one does, and it is not the primary metric.
"""

import numpy as np

from ..ab import ab_run, no_effect

NAME = "many-metrics"
ABOUT = "A new product page layout with no real effect, checked on 20 metrics (planted: one false winner)"
DEFAULT_SEED = 2001  # chosen: exactly one of the 20 metrics has p < 0.05 (reference/c40/measure/find_seeds.py)
CUSTOMERS = 60_000
METRICS = ["revenue", "orders", "converted", "returns", "visits", "pages_viewed", "add_to_cart", "wishlist_adds",
           "reviews_read", "search_uses", "newsletter_signups", "minutes_on_site", "support_contacts",
           "coupon_uses", "share_clicks", "photo_zooms", "size_guide_views", "video_plays", "compare_uses",
           "stock_alerts"]


def run(seed, customers=None):
    tables, truth, _ = ab_run(seed, customers or CUSTOMERS, 28, no_effect)
    c = tables["customers"]
    rng = np.random.default_rng(seed + 1)
    v = c["visits"].to_numpy()
    engaged = rng.lognormal(0, 0.5, len(c))  # one hidden "how engaged" value makes the metrics correlated
    rates = {"pages_viewed": 4.0, "add_to_cart": 0.35, "wishlist_adds": 0.08, "reviews_read": 0.6, "search_uses": 0.9,
             "newsletter_signups": 0.005, "support_contacts": 0.02, "coupon_uses": 0.03, "share_clicks": 0.01,
             "photo_zooms": 0.7, "size_guide_views": 0.05, "video_plays": 0.12, "compare_uses": 0.06,
             "stock_alerts": 0.015}
    for name, r in rates.items():
        c[name] = rng.poisson(v * r * engaged)
    c["minutes_on_site"] = np.round(rng.gamma(2.0, 2.5 * engaged * v), 1)
    c["converted"] = (c["orders"] > 0).astype(int)
    tables["customers"] = c
    truth = {m: {"effect": 0.0, "unit": "every metric: no real effect"} for m in METRICS}
    truth["planted"] = "The layout changes nothing. Any 'winner' among the 20 metrics is chance."
    meta = {"about": ABOUT, "unit": "customer", "days": 28, "start": "2025-09-08", "end": "2025-10-05",
            "variants": {"A": "today's product page", "B": "the new layout"}, "primary_metric": "revenue",
            "metrics": METRICS, "split": 0.5}
    return tables, truth, meta
