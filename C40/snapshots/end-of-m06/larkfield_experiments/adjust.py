"""Adjusting for confounders in observational data: regression, propensity scores, matching and weighting.

Each function returns a dict with the estimate and its 95% interval. The confounders are the columns that cause
both the treatment and the outcome (from the causal graph of Module 1)."""

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

CONFOUNDERS = ["pre_spend", "pre_orders", "visits", "tenure_days", "new_customer", "desktop"]


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["desktop"] = (d["device"] == "desktop").astype(int)
    return d


def regression(d, treatment, outcome, covariates):
    f = f"{outcome} ~ {treatment}" + "".join(f" + {c}" for c in covariates)
    m = smf.ols(f, data=d).fit(cov_type="HC1")
    b, se = m.params[treatment], m.bse[treatment]
    return {"method": "regression", "estimate": float(b), "low": float(b - 1.96 * se), "high": float(b + 1.96 * se),
            "target": "ATE"}


def propensity(d, treatment, covariates):
    x = sm.add_constant(d[covariates].astype(float).assign(
        **{c: np.log1p(d[c]) for c in covariates if c in ("pre_spend", "visits", "tenure_days", "pre_orders")}))
    return sm.Logit(d[treatment], x).fit(disp=0).predict(x).to_numpy()


def smd(d, treatment, covariates, w=None):
    """Standardised mean differences (treated − control) / pooled sd, with optional weights."""
    w = np.ones(len(d)) if w is None else w
    t = d[treatment].to_numpy() == 1
    out = {}
    for c in covariates:
        x = d[c].to_numpy(float)
        m1, m0 = np.average(x[t], weights=w[t]), np.average(x[~t], weights=w[~t])
        out[c] = float((m1 - m0) / np.sqrt((x[t].var() + x[~t].var()) / 2))
    return out


def ipw(d, treatment, outcome, ps, n_boot=200, seed=0):
    """Inverse probability weighting (ATE, normalised weights); the interval comes from a bootstrap."""
    def est(idx):
        t, y, p = d[treatment].to_numpy()[idx], d[outcome].to_numpy()[idx], ps[idx]
        w1, w0 = t / p, (1 - t) / (1 - p)
        return (w1 * y).sum() / w1.sum() - (w0 * y).sum() / w0.sum()
    rng = np.random.default_rng(seed)
    n = len(d)
    point = est(np.arange(n))
    boots = [est(rng.integers(0, n, n)) for _ in range(n_boot)]
    low, high = np.percentile(boots, [2.5, 97.5])
    return {"method": "weighting (IPW)", "estimate": float(point), "low": float(low), "high": float(high),
            "target": "ATE"}


def match(d, treatment, outcome, ps, caliper=0.05):
    """Nearest-neighbour matching on the propensity score (with replacement): each treated customer gets the
    control customer with the closest score, within the caliper (in standard deviations of the score's logit).
    Estimates the effect on the treated (ATT); the interval uses the matched pairs' spread (a simple version)."""
    logit = np.log(ps / (1 - ps))
    t = d[treatment].to_numpy() == 1
    y = d[outcome].to_numpy()
    lt, lc = logit[t], logit[~t]
    order = np.argsort(lc)
    pos = np.clip(np.searchsorted(lc[order], lt), 1, len(lc) - 1)
    left, right = order[pos - 1], order[pos]
    best = np.where(np.abs(lc[left] - lt) <= np.abs(lc[right] - lt), left, right)
    ok = np.abs(lc[best] - lt) <= caliper * logit.std()
    diffs = y[t][ok] - y[~t][best[ok]]
    se = diffs.std(ddof=1) / np.sqrt(len(diffs))
    return {"method": "matching (nearest neighbour)", "estimate": float(diffs.mean()),
            "low": float(diffs.mean() - 1.96 * se), "high": float(diffs.mean() + 1.96 * se), "target": "ATT",
            "matched": int(ok.sum()), "unmatched": int((~ok).sum()),
            "controls_used": int(len(np.unique(best[ok])))}
