"""A small synthetic control: a weighted mix of other units that follows the treated unit before the change.

The weights are not negative and add up to 1, and they minimise the squared gap to the treated unit's (log)
sales in the weeks before the change. After the change, the mix is the estimate of "the treated unit without the
change". Abadie, Diamond and Hainmueller (2010) describe the full method; this version uses only the outcome.
"""

import numpy as np
from scipy.optimize import minimize


def synth_weights(treated_pre: np.ndarray, donors_pre: np.ndarray) -> np.ndarray:
    """treated_pre: (weeks,); donors_pre: (weeks, donors). Returns the donor weights."""
    k = donors_pre.shape[1]
    loss = lambda w: float(((treated_pre - donors_pre @ w) ** 2).sum())  # noqa: E731
    res = minimize(loss, np.full(k, 1 / k), method="SLSQP", bounds=[(0, 1)] * k,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}], options={"maxiter": 500, "ftol": 1e-12})
    w = np.clip(res.x, 0, None)
    return w / w.sum()


def synth_effect(series: dict, treated: str, pre: np.ndarray) -> dict:
    """series: unit -> log sales (same weeks); pre: True for the weeks before the change."""
    donors = [u for u in series if u != treated]
    y = series[treated]
    x = np.column_stack([series[u] for u in donors])
    x_mean, y_mean = x[pre].mean(axis=0), y[pre].mean()
    w = synth_weights(y[pre] - y_mean, x[pre] - x_mean)  # match the shape, not the level
    synth = (x - x_mean) @ w + y_mean
    gap = y - synth
    rmspe_pre = float(np.sqrt((gap[pre] ** 2).mean()))
    rmspe_post = float(np.sqrt((gap[~pre] ** 2).mean()))
    return {"weights": dict(zip(donors, map(float, w))), "effect": float(np.expm1(gap[~pre].mean())),
            "rmspe_pre": rmspe_pre, "ratio": rmspe_post / rmspe_pre, "gap": gap.tolist()}
