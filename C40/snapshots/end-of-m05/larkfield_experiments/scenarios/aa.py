"""An A/A test: both groups see the same shop. Any difference is noise, so it checks the test system itself."""

from ..ab import ab_run, no_effect

NAME = "aa"
ABOUT = "An A/A test: both groups get today's shop, 28 days. The true effect is zero"
DEFAULT_SEED = 41
CUSTOMERS = 200_000


def run(seed, customers=None):
    tables, truth, _ = ab_run(seed, customers or CUSTOMERS, 28, no_effect)
    meta = {"about": ABOUT, "unit": "customer", "days": 28, "start": "2025-09-08", "end": "2025-10-05",
            "variants": {"A": "today's shop", "B": "today's shop (the same)"}, "primary_metric": "revenue",
            "guardrails": ["return_rate"], "split": 0.5}
    return tables, truth, meta
