"""Confidence: is it true (calibration), and three zones that use it: decide, review, send to a person."""

import numpy as np
import pandas as pd

from larkroute import costs as cost_table


def reliability(confidence, correct, bins: int = 10) -> tuple[pd.DataFrame, float]:
    """The reliability table (mean confidence and accuracy per bin) and the expected calibration error (ECE)."""
    conf, ok = np.asarray(confidence, float), np.asarray(correct, bool)
    edges = np.linspace(0, 1, bins + 1)
    rows, ece = [], 0.0
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        m = (conf >= lo) & ((conf < hi) | (hi == 1.0))
        if m.any():
            rows.append({"bin": f"{lo:.1f}-{hi:.1f}", "messages": int(m.sum()),
                         "mean_confidence": round(conf[m].mean(), 3), "accuracy": round(ok[m].mean(), 3)})
            ece += m.mean() * abs(conf[m].mean() - ok[m].mean())
    return pd.DataFrame(rows), round(float(ece), 4)


def decide(proba: pd.DataFrame, high: float, low: float) -> pd.Series:
    """The route when the top probability is at least `high`; "review" between `low` and `high`; "needs_person"
    (a senior person reads it first) below `low`."""
    p, r = proba.max(axis=1), proba.idxmax(axis=1)
    return pd.Series(np.where(p >= high, r, np.where(p >= low, "review", "needs_person")), index=proba.index)


def report(truth: pd.DataFrame, routed: pd.Series, costs: dict) -> dict:
    auto = ~routed.isin(["review", "needs_person"])
    return {"decide": round(auto.mean(), 3), "review": round((routed == "review").mean(), 3),
            "person": round((routed == "needs_person").mean(), 3),
            "error_rate_decide": round((routed[auto] != truth["route"][auto]).mean(), 4) if auto.any() else None,
            "cost_per_1000": round(cost_table.total(truth, routed, costs) / len(truth) * 1000, 1)}


GRID = np.round(np.arange(0.30, 1.0001, 0.01), 2)


def choose(truth: pd.DataFrame, proba: pd.DataFrame, costs: dict, review_max: float,
           grid=GRID) -> tuple[float, float, dict]:
    """The thresholds with the lowest cost whose review and person zones together stay under review_max."""
    best = None
    for high in grid:
        for low in np.concatenate([[0.0], grid[grid < high][::5]]):
            rep = report(truth, decide(proba, high, low), costs)
            if rep["review"] + rep["person"] > review_max:
                continue
            if best is None or rep["cost_per_1000"] < best[2]["cost_per_1000"]:
                best = (float(high), float(low), rep)
    if best is None:
        raise ValueError(f"no thresholds keep the review load under {review_max:.0%}")
    return best
