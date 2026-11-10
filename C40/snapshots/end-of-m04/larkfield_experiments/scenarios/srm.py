"""The free-delivery test with a redirect bug (a practice problem we made on purpose).

Version B is served after a redirect. On slow mobile connections, the redirect fails and the customer leaves
before the page loads, so the log never sees them. The split should be 50/50; it arrives as about 52/48. The
customers who are lost are not random: they visit less and buy less, so B looks better than it is.
"""

import numpy as np

from ..ab import ab_run
from .delivery import effect

NAME = "srm"
ABOUT = "The free-delivery test with a redirect bug that loses some B customers (planted): a 52/48 split"
DEFAULT_SEED = 40
CUSTOMERS = 200_000


def lose(pop, variant, rng):
    slow = (pop.device == "mobile") & (pop.activity < np.median(pop.activity)) & (rng.random(len(pop)) < 0.62)
    lost = slow & (variant == 1)
    return lambda idx, first: lost[idx]


def run(seed, customers=None):
    tables, truth, _ = ab_run(seed, customers or CUSTOMERS, 28, effect, lose=lose)
    c = tables["customers"]
    truth["planted"] = ("A redirect bug loses B customers on slow mobile connections. They visit and buy less "
                        "than average, so the B group that the log sees is better than the real B group.")
    truth["share_b_seen"] = round(float((c["variant"] == "B").mean()), 4)
    meta = {"about": ABOUT, "unit": "customer", "days": 28, "start": "2025-09-08", "end": "2025-10-05",
            "variants": {"A": "free delivery from 75 dollars (today)", "B": "free delivery from 50 dollars"},
            "primary_metric": "revenue", "guardrails": ["return_rate"], "split": 0.5,
            "covariate": "pre_spend (spending in the 8 weeks before the test)"}
    return tables, truth, meta
