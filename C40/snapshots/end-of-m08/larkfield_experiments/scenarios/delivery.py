"""Free delivery from 50 dollars instead of 75 (Hana's test). Randomised by customer, 28 days."""

from ..ab import ab_run
from ..world import Effect

NAME = "delivery"
ABOUT = "Free delivery from 50 dollars instead of 75: an A/B test by customer, 28 days"
DEFAULT_SEED = 40
CUSTOMERS = 200_000
# The true change (synthetic): more visits end with an order, orders are a little smaller, more are returned.
CONV, BASKET, RETURNS = 1.045, 0.985, 0.012


def effect(idx, day, since):
    return Effect(conv=CONV, basket=BASKET, returns=RETURNS)


def run(seed, customers=None):
    tables, truth, _ = ab_run(seed, customers or CUSTOMERS, 28, effect)
    meta = {"about": ABOUT, "unit": "customer", "days": 28, "start": "2025-09-08", "end": "2025-10-05",
            "variants": {"A": "free delivery from 75 dollars (today)", "B": "free delivery from 50 dollars"},
            "primary_metric": "revenue", "guardrails": ["return_rate"], "split": 0.5,
            "covariate": "pre_spend (spending in the 8 weeks before the test)"}
    return tables, truth, meta
