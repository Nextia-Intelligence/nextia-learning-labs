"""A new checkout button that does nothing (a practice problem we made on purpose).

The team looked at the dashboard every day and stopped the test on day 3, when B was "winning" with p < 0.05.
The simulator ran all 28 days anyway, so you can see what happened next. The true effect is zero.
"""

from ..ab import ab_run, no_effect

NAME = "early-stop"
ABOUT = "A new checkout button with no real effect, stopped on day 3 when it looked like a win (planted)"
DEFAULT_SEED = 1197  # chosen because day 3 shows a "win" with this seed (reference/c40/measure/find_seeds.py)
CUSTOMERS = 60_000


def run(seed, customers=None):
    tables, truth, _ = ab_run(seed, customers or CUSTOMERS, 28, no_effect)
    truth["planted"] = "The team stopped on day 3 at the first p < 0.05. The true effect is zero."
    meta = {"about": ABOUT, "unit": "customer", "days": 28, "start": "2025-09-08", "end": "2025-10-05",
            "variants": {"A": "today's checkout button", "B": "a new green checkout button"},
            "primary_metric": "revenue", "split": 0.5, "stopped_on_day": 3}
    return tables, truth, meta
