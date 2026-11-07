"""Drift checks on the scores: does this week look like the validation week?"""
import numpy as np


def psi(expected, actual, bins=10):
    """Population stability index of `actual` against `expected` (bins from the quantiles of `expected`)."""
    e = np.asarray(expected, float)
    a = np.asarray(actual, float)
    edges = np.unique(np.quantile(e, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    pe = np.histogram(e, edges)[0] / len(e)
    pa = np.histogram(a, edges)[0] / len(a)
    pe, pa = np.clip(pe, 1e-4, None), np.clip(pa, 1e-4, None)
    return float(((pa - pe) * np.log(pa / pe)).sum())


def alarms(week, scores, reference, check_share, budget_share, psi_limit=0.25):
    out = []
    p = psi(reference, scores)
    if p > psi_limit:
        out.append(f"scores moved (PSI {p:.2f} > {psi_limit})")
    if check_share > budget_share:
        out.append(f"checks {check_share:.0%} of photos, budget {budget_share:.0%}")
    return p, out
