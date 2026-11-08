"""CUPED: use each customer's spending before the test to remove part of the noise.

    adjusted = outcome − theta × (before − mean of before),  theta = cov(outcome, before) / var(before)

theta is computed on both groups together, so the adjustment is the same for A and B, and the difference of
the adjusted means estimates the same effect with a smaller variance.
"""

import numpy as np


def cuped_adjust(y, x):
    y, x = np.asarray(y, float), np.asarray(x, float)
    theta = np.cov(y, x, ddof=1)[0, 1] / x.var(ddof=1)
    return y - theta * (x - x.mean()), float(theta)


def variance_reduction(y, x) -> float:
    """The share of the variance that CUPED removes: the squared correlation of outcome and covariate."""
    return float(np.corrcoef(y, x)[0, 1] ** 2)
