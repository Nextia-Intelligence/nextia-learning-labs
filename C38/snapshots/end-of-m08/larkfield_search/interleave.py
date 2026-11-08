"""Test changes online (Module 8, lesson 2): team-draft interleaving and an A/B test, simulated with the click model.

Nobody clicks in a simulation: the click model of clicks.py does, with the judgments as the truth. So this shows
how many searches each kind of online test needs to see a difference that the judgments say is there; it does not
show how real people behave.
"""

import math

import numpy as np

from . import clicks, data, runs


def team_draft(a, b, rng, n=10):
    """Team-draft interleaving: A and B take turns (a coin decides who starts each round) to add their best
    product that is not shown yet. Returns the list and the team of each position."""
    out, team, ia, ib = [], [], 0, 0
    while len(out) < n and (ia < len(a) or ib < len(b)):
        order = ("A", "B") if rng.random() < 0.5 else ("B", "A")
        for t in order:
            src = a if t == "A" else b
            i = ia if t == "A" else ib
            while i < len(src) and src[i] in out:
                i += 1
            if i < len(src) and len(out) < n:
                out.append(src[i])
                team.append(t)
                i += 1
            if t == "A":
                ia = i
            else:
                ib = i
    return out, team


def sign_test_p(wins_a, wins_b):
    """Two-sided p-value that A and B win equally often (normal approximation of the binomial)."""
    n = wins_a + wins_b
    if n == 0:
        return 1.0
    z = (abs(wins_a - wins_b) - 1) / math.sqrt(n)
    return math.erfc(max(z, 0) / math.sqrt(2))


def two_proportion_p(x1, n1, x2, n2):
    if min(n1, n2) == 0:
        return 1.0
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) or 1e-12
    return math.erfc(abs(x1 / n1 - x2 / n2) / se / math.sqrt(2))


def ranked_lists(run_a, run_b, split="test"):
    q = data.split(split)
    q = q[q["source"].isin(["wands", "translated", "typo", "code"])]
    fa, fb = runs.get(run_a), runs.get(run_b)
    lists = {}
    for qid, text in zip(q["query_id"], q["query"]):
        lists[qid] = ([p for p, _ in fa(text, qid, 10)], [p for p, _ in fb(text, qid, 10)])
    return lists


def simulate(lists, seed=0, max_searches=20000, alpha=0.05):
    """Searches until each test is clear (p < alpha), checked every 100 searches; a random test query per search.
    Returns {'interleaving': n or None, 'ab': n or None, 'winner_interleaving': 'A'/'B'/None, ...}."""
    rng = np.random.default_rng(seed)
    j = data.judgments()
    qids = list(lists)
    wa = wb = 0
    ab = {"A": [0, 0], "B": [0, 0]}  # searches with a click, searches
    out = {"interleaving": None, "ab": None}
    for s in range(1, max_searches + 1):
        qid = qids[rng.integers(len(qids))]
        a, b = lists[qid]
        shown, team = team_draft(a, b, rng)
        c, _ = clicks.simulate(shown, j.get(qid, {}), rng)
        ca = sum(ci for ci, t in zip(c, team) if t == "A")
        cb = sum(ci for ci, t in zip(c, team) if t == "B")
        wa += ca > cb
        wb += cb > ca
        arm = "A" if rng.random() < 0.5 else "B"
        c2, _ = clicks.simulate(a if arm == "A" else b, j.get(qid, {}), rng)
        ab[arm][0] += sum(c2) > 0
        ab[arm][1] += 1
        if s % 100 == 0:
            if out["interleaving"] is None and sign_test_p(wa, wb) < alpha:
                out["interleaving"], out["winner_interleaving"] = s, "A" if wa > wb else "B"
            if out["ab"] is None and two_proportion_p(*ab["A"], *ab["B"]) < alpha:
                out["ab"] = s
                out["winner_ab"] = "A" if ab["A"][0] / ab["A"][1] > ab["B"][0] / ab["B"][1] else "B"
            if out["interleaving"] and out["ab"]:
                break
    out.update({"wins_a": wa, "wins_b": wb, "ab_click_rate_a": ab["A"][0] / max(ab["A"][1], 1),
                "ab_click_rate_b": ab["B"][0] / max(ab["B"][1], 1), "searches": s})
    return out
