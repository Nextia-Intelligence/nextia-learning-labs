"""A sequential test that allows a look every day: the mixture sequential probability ratio test (mSPRT) of
Johari, Pekelis and Walsh (2015), for a difference of means with a normal approximation.

In plain words: a normal test spends its 5% error once, at the end. If you look every day and stop at the first
p < 0.05, you spend it again at every look, and false winners pile up. The always-valid interval is wider at
each look, by just enough that the chance of EVER excluding the true effect, over all the looks, stays at 5%.

    V = the variance of the difference (se squared), tau2 = the mixing variance (a guess at the size of real
    effects, squared). The interval at a look is: difference ± sqrt(V (V + tau2) / tau2 × (2 log(1/alpha) +
    log((V + tau2) / V))). Keep the running intersection of the intervals: once a value is out, it stays out.
"""

import math

import numpy as np


def always_valid_halfwidth(v: float, tau2: float, alpha: float = 0.05) -> float:
    return math.sqrt(v * (v + tau2) / tau2 * (2 * math.log(1 / alpha) + math.log((v + tau2) / v)))


def always_valid_p(diff: float, v: float, tau2: float) -> float:
    """1 / (the mixture likelihood ratio against "no effect"), capped at 1."""
    lr = math.sqrt(v / (v + tau2)) * math.exp(diff**2 * tau2 / (2 * v * (v + tau2)))
    return min(1.0, 1.0 / lr)


def sequential_path(diffs, variances, tau2, alpha=0.05):
    """The always-valid intervals and p-values along a series of looks (running intersection and minimum)."""
    lo, hi, pmin = -np.inf, np.inf, 1.0
    out = []
    for d, v in zip(diffs, variances):
        if not v > 0:
            out.append((lo, hi, pmin))
            continue
        h = always_valid_halfwidth(v, tau2, alpha)
        lo, hi = max(lo, d - h), min(hi, d + h)
        pmin = min(pmin, always_valid_p(d, v, tau2))
        out.append((lo, hi, pmin))
    return out
