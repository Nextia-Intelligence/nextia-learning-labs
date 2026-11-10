"""Free delivery in Quebec first: weekly sales of 60 delivery areas in 10 provinces, June 2024 to November 2025.

Larkfield started free delivery from 50 dollars in Quebec on Monday 2 June 2025, for business reasons (no coin
flip). The other provinces kept the old rule. The true effect on Quebec's sales is known to the simulator.

The provinces share a national pattern (the season, the economy), and an eastern trend that Quebec shares with
the Atlantic provinces more than with Ontario. So Ontario alone is not a perfect comparison for Quebec.
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from ..world import season

NAME = "regions"
ABOUT = "Free delivery in Quebec first (from 2 June 2025): weekly sales of 60 areas in 10 provinces (no test)"
DEFAULT_SEED = 40
CUSTOMERS = None
START, WEEKS = date(2024, 6, 3), 78  # to the week of 24 November 2025
ROLLOUT = date(2025, 6, 2)
EFFECT = 0.06  # +6% on Quebec's weekly sales
AREAS = {"ON": 14, "QC": 10, "BC": 8, "AB": 8, "MB": 4, "SK": 4, "NS": 4, "NB": 3, "NL": 3, "PE": 2}
EAST = {"ON": 0.0, "QC": 0.6, "BC": 0.1, "AB": -0.2, "MB": 0.3, "SK": 0.2, "NS": 0.9, "NB": 1.0, "NL": 1.1, "PE": 0.8}
SIZE = {"ON": 1.0, "QC": 0.85, "BC": 0.9, "AB": 0.8, "MB": 0.6, "SK": 0.55, "NS": 0.5, "NB": 0.45, "NL": 0.4,
        "PE": 0.35}


def run(seed, customers=None):
    rng = np.random.default_rng(seed)
    weeks = [START + timedelta(weeks=i) for i in range(WEEKS)]
    post = np.array([w >= ROLLOUT for w in weeks])
    national = np.log([np.mean([season(w + timedelta(days=k)) for k in range(7)]) for w in weeks])
    national = national + np.cumsum(rng.normal(0.0015, 0.006, WEEKS))
    east = np.cumsum(rng.normal(-0.0012, 0.004, WEEKS))  # the eastern trend
    rows, cf = [], []
    for prov, k in AREAS.items():
        prov_noise = rng.normal(0, 0.012, WEEKS)
        for a in range(1, k + 1):
            level = np.log(26_000 * SIZE[prov]) + rng.normal(0, 0.25)
            log0 = level + national + EAST[prov] * east + prov_noise + rng.normal(0, 0.03, WEEKS)
            rev0 = np.exp(log0)
            treated = (prov == "QC") & post
            rev = rev0 * np.where(treated, 1 + EFFECT, 1.0)
            area = f"{prov}-{a:02d}"
            rows.append(pd.DataFrame({"week": [w.isoformat() for w in weeks], "province": prov, "area": area,
                                      "revenue": np.round(rev, 2), "free_delivery_50": treated.astype(int)}))
            cf.append(pd.DataFrame({"week": [w.isoformat() for w in weeks], "area": area,
                                    "revenue_without_change": np.round(rev0, 2)}))
    areas = pd.concat(rows, ignore_index=True)
    counter = pd.concat(cf, ignore_index=True)
    provinces = areas.groupby(["week", "province"], as_index=False).agg(revenue=("revenue", "sum"),
                                                                        free_delivery_50=("free_delivery_50", "max"))
    qc_post = areas[(areas.province == "QC") & (areas.week >= ROLLOUT.isoformat())]
    qc_cf = counter[counter.area.str.startswith("QC") & (counter.week >= ROLLOUT.isoformat())]
    truth = {"rollout": ROLLOUT.isoformat(), "treated": "QC",
             "effect": {"relative": EFFECT, "dollars_per_week": round(float((qc_post.revenue.sum()
                                                                            - qc_cf.revenue_without_change.sum())
                                                                           / post.sum()), 2),
                        "unit": "Quebec's weekly sales after the rollout"},
             "note": "Quebec shares an eastern trend with the Atlantic provinces (60% of it); Ontario does not."}
    meta = {"about": ABOUT, "unit": "area-week", "start": START.isoformat(), "end": weeks[-1].isoformat(),
            "events": {"rollout": ROLLOUT.isoformat(), "treated": "QC"},
            "note": "counterfactual.csv is the simulator's truth: Quebec's areas without the change."}
    return {"areas_weekly": areas, "provinces_weekly": provinces, "counterfactual": counter}, truth, meta
