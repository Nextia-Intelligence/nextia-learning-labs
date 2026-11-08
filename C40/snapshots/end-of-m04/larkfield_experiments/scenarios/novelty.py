"""A new "bought together" widget that wins at first and then loses (a practice problem we made on purpose).

Customers click the new widget because it is new. After about two weeks of seeing it, they ignore it, and it
takes space from the products they came for. The true effect depends on the days since a customer first saw it:
about +10% on the chance to order in the first days, then below zero after two weeks.
"""

import numpy as np

from ..ab import ab_run
from ..world import Effect

NAME = "novelty"
ABOUT = "A new 'bought together' widget, 6 weeks: it wins at first, then loses (planted novelty effect)"
DEFAULT_SEED = 40
CUSTOMERS = 120_000


def conv_lift(since):
    return 1 + 0.12 * np.exp(-since / 5.0) - 0.03


def effect(idx, day, since):
    return Effect(conv=conv_lift(since))


def run(seed, customers=None):
    tables, truth, (outcomes, hidden) = ab_run(seed, customers or CUSTOMERS, 42, effect, potentials=True)
    hidden["week_since_first"] = hidden["_since"] // 7 + 1
    by = hidden.groupby("week_since_first")[["_rev0", "_rev1"]].mean()
    truth["by_week_since_first_visit"] = {
        str(int(w)): {"revenue_per_visit_effect": round(float(r._rev1 - r._rev0), 4),
                      "relative": round(float(r._rev1 / r._rev0 - 1), 4)} for w, r in by.iterrows()}
    truth["planted"] = "A novelty effect: the widget helps in a customer's first days with it, then hurts."
    meta = {"about": ABOUT, "unit": "customer", "days": 42, "start": "2025-09-08", "end": "2025-10-19",
            "variants": {"A": "today's product page", "B": "the page with the 'bought together' widget"},
            "primary_metric": "revenue", "split": 0.5}
    return tables, truth, meta
