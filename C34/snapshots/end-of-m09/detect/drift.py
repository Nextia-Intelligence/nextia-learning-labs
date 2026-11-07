"""Has "normal" moved? Compare the last days with the model's training days (Module 3's checks, on a schedule)."""
import numpy as np
import pandas as pd

from . import features
from . import model as model_mod
from .alerts import above_threshold


def psi(ref, cur, bins=10):
    """Population Stability Index of a number: 0.1 and 0.25 are the common limits (only conventions)."""
    ref, cur = np.asarray(ref, float), np.asarray(cur, float)
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:                         # a 0/1 feature: compare the share of ones
        r = np.array([np.mean(ref == 0), np.mean(ref != 0)])
        c = np.array([np.mean(cur == 0), np.mean(cur != 0)])
    else:
        edges[0], edges[-1] = -np.inf, np.inf
        r = np.histogram(ref, edges)[0] / len(ref)
        c = np.histogram(cur, edges)[0] / len(cur)
    r, c = np.clip(r, 1e-4, None), np.clip(c, 1e-4, None)
    return float(np.sum((c - r) * np.log(c / r)))


def check(p, model, day, days=7, budget=50, history_days=60):
    """PSI of each feature and of the amount, and the pressure: customers above the training threshold per day."""
    last = pd.Timestamp(day)
    first = (last - pd.Timedelta(days=days - 1)).date()
    ref = model_mod.behaviour_with_history(p, model.first_day, model.last_day, history_days)
    cur = model_mod.behaviour_with_history(p, first, last.date(), history_days)
    rows = [{"feature": f, "psi": round(psi(ref[f], cur[f]), 3)} for f in features.BEHAVIOUR + ["amount"]]
    cur = cur.assign(score=model.score(cur), day=cur.ts.dt.floor("D"))
    pressure = cur.groupby("day").apply(lambda g: above_threshold(g, model.fixed_threshold), include_groups=False)
    return pd.DataFrame(rows), pressure


def verdict(psi_table, pressure, budget):
    """A short decision for the person who approves a new threshold or a retrained model."""
    big = psi_table[psi_table.psi >= 0.25].feature.tolist()
    days_over = int((pressure > 2 * budget).sum())
    if days_over >= 3:
        return (f"Normal has moved: on {days_over} of the last {len(pressure)} days, more than twice the budget "
                f"scored above the training threshold. Drift (PSI 0.25 or more): {', '.join(big) or 'none'}. "
                "Retrain on recent days, then ask the fraud lead to approve the new model.")
    if big:
        return (f"Some features moved (PSI 0.25 or more: {', '.join(big)}), but the alert pressure is normal. "
                "Look at the change; no retraining needed yet.")
    return "No drift that matters: keep the model."
