"""The support assistant's new prompt (B) against today's prompt (A): an online test by customer, 14 days.

Each ticket is one of the 120 support questions. The assistant's answer is the recorded answer of a language
model (Azure chat-small) to that question with prompt A or B: nothing is generated now. Simulated customers react
to the answer: a correct answer resolves the ticket most of the time; a wrong one often ends with a request for a
person; a hand-off costs an agent's time.
"""

import numpy as np
import pandas as pd

from ..support import graded

NAME = "prompt"
ABOUT = "The support assistant's new prompt against today's, with recorded answers: a test by customer, 14 days"
DEFAULT_SEED = 40
CUSTOMERS = 9_000
AGENT_COST = 6.50  # dollars of an agent's time per ticket handed over (an assumption)
WEIGHTS = {"delivery_time": 0.18, "returns": 0.12, "refund_time": 0.12, "delivery_cost": 0.08, "change_order": 0.10,
           "damaged_small": 0.08, "return_cost": 0.06, "price_match": 0.04, "gift_card": 0.03, "gold": 0.04,
           "handoff_security": 0.04, "handoff_double": 0.05, "handoff_damaged_big": 0.03, "handoff_legal": 0.03}


def run(seed, customers=None):
    rng = np.random.default_rng(seed)
    n = customers or CUSTOMERS
    g = pd.DataFrame(graded())
    by = {v: g[g.prompt == v].set_index("id") for v in ("A", "B")}
    ids = by["A"].index.to_numpy()
    cat = by["A"]["category"].to_numpy()
    w = np.array([WEIGHTS[c] for c in cat])
    w = w / w.sum()
    variant = rng.random(n) < 0.5
    k = rng.poisson(1.35, n) + 1
    cust = np.repeat(np.arange(n), k)
    m = len(cust)
    q = rng.choice(len(ids), size=m, p=w)
    u1, u2, u3 = rng.random(m), rng.random(m), rng.random(m)
    worlds = {}
    for v in ("A", "B"):
        a = by[v].loc[ids[q]]
        handoff0 = a["handoff"].to_numpy() == 1
        correct = a["correct"].to_numpy() == 1
        resolved = ~handoff0 & (u1 < np.where(correct, 0.88, 0.30))
        handoff = handoff0 | (~resolved & (u2 < 0.75))
        complaint = u3 < 0.01 + 0.06 * ~resolved + 0.08 * a["unsafe"].to_numpy()
        cost = a["model_cost"].to_numpy() + AGENT_COST * handoff
        worlds[v] = pd.DataFrame({"resolved": resolved.astype(int), "handoff": handoff.astype(int),
                                  "complaint": complaint.astype(int), "cost": np.round(cost, 5)})
    is_b = variant[cust]
    obs = pd.DataFrame({c: np.where(is_b, worlds["B"][c], worlds["A"][c]) for c in worlds["A"].columns})
    start = pd.Timestamp("2025-10-20")
    tickets = pd.DataFrame({"ticket_id": np.arange(1, m + 1),
                            "date": (start + pd.to_timedelta(rng.integers(0, 14, m), unit="D")).strftime("%Y-%m-%d"),
                            "customer_id": [f"S{i:05d}" for i in cust + 1], "variant": np.where(variant[cust], "B", "A"),
                            "question_id": ids[q], "category": cat[q], **{c: obs[c].to_numpy() for c in obs.columns}})
    truth = {}
    for c in ("resolved", "handoff", "complaint", "cost"):
        a0, b1 = worlds["A"][c].mean(), worlds["B"][c].mean()
        truth[c] = {"control_world": round(float(a0), 5), "treated_world": round(float(b1), 5),
                    "effect": round(float(b1 - a0), 5), "unit": "per ticket"}
    meta = {"about": ABOUT, "unit": "customer (tickets are grouped by customer)", "days": 14, "start": "2025-10-20",
            "end": "2025-11-02", "variants": {"A": "today's prompt", "B": "the new prompt"}, "split": 0.5,
            "primary_metric": "resolved", "guardrails": ["complaint"], "agent_cost": AGENT_COST,
            "answers": "recorded answers of Azure chat-small (two prompts, 120 questions), replayed"}
    return {"tickets": tickets}, truth, meta
