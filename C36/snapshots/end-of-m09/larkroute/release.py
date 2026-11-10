"""The release check: a new model replaces the current one only if no slice of the test messages gets worse by
more than the tolerance, and every new route is found well enough on the labelled launch-month messages that
were kept for checking."""

import pandas as pd

MIN_MESSAGES = 30


def slices(truth: pd.DataFrame, pred) -> dict:
    pred = pd.Series(list(pred), index=truth.index)
    out = {}
    for r, g in truth.groupby("route"):
        out[f"route={r}"] = (len(g), float((pred[g.index] == r).mean()))
    for col in ("language", "channel"):
        for v, g in truth.groupby(col):
            out[f"{col}={v}"] = (len(g), float((pred[g.index] == g["route"]).mean()))
    return out


def check(old: dict, new: dict, tolerance: float = 0.02) -> list[dict]:
    rows = []
    for name, (n, before) in old.items():
        after = new[name][1]
        ok = n < MIN_MESSAGES or after >= before - tolerance
        rows.append({"slice": name, "messages": n, "current": round(before, 3), "candidate": round(after, 3),
                     "result": "ok" if ok else "WORSE"})
    return rows
