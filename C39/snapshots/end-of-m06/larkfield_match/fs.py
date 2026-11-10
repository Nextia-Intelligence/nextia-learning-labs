"""The Fellegi–Sunter idea, computed by hand from labelled pairs (Module 5, lesson 1).

For each field, a pair falls into one agreement level (for example: same surname, similar surname, different).
m = P(level | the two records are the same entity); u = P(level | they are not).
The match weight of the level is log2(m / u): positive when the level is more common for true matches.
A pair's total weight is the prior weight log2(p / (1 - p)) plus the weights of its levels.
"""

import math

import numpy as np
import pandas as pd

from . import evaluate, prepared

# field -> (vector column, [(level name, lowest value)]) ; a value below every level is "different"
LEVELS = {
    "first": ("first_jw", [("same", 1.0), ("close (JW >= 0.92)", 0.92), ("similar (JW >= 0.8)", 0.8)]),
    "last": ("last_jw", [("same", 1.0), ("close (JW >= 0.92)", 0.92)]),
    "email": ("email_eq", [("same", 1.0)]),
    "phone": ("phone_eq", [("same", 1.0)]),
    "postcode": ("postcode_eq", [("same", 1.0)]),
    "street": ("street_tsr", [("same", 1.0), ("similar (>= 0.9)", 0.9)]),
    "town": ("town_eq", [("same", 1.0)]),
    "dob": ("dob_eq", [("same", 1.0)]),
}


def level_of(values, levels):
    """The level name of each value; 'missing' for NaN, 'different' below every level."""
    out = np.full(len(values), "different", dtype=object)
    v = np.asarray(values, dtype="float64")
    for name, low in reversed(levels):
        out[v >= low - 1e-9] = name
    out[np.isnan(v)] = "missing"
    return out


def estimate(vectors_df, labels):
    """m and u of every level of every field, from pairs with known labels (1 same, 0 different)."""
    rows = []
    lab = np.asarray(labels)
    for field, (col, levels) in LEVELS.items():
        lv = level_of(vectors_df[col], levels)
        for name in [n for n, _ in levels] + ["different"]:
            present = lv != "missing"
            m = ((lv == name) & (lab == 1)).sum() / max(((lab == 1) & present).sum(), 1)
            u = ((lv == name) & (lab == 0)).sum() / max(((lab == 0) & present).sum(), 1)
            rows.append({"field": field, "level": name, "m": m, "u": u,
                         "weight": math.log2(max(m, 1e-6) / max(u, 1e-6))})
    return pd.DataFrame(rows)


def score(vectors_df, table, prior):
    """Total match weight and match probability of each pair (missing values add 0)."""
    total = np.full(len(vectors_df), math.log2(prior / (1 - prior)))
    w = table.set_index(["field", "level"]).weight
    for field, (col, levels) in LEVELS.items():
        lv = pd.Series(level_of(vectors_df[col], levels))
        weights = {lvl: wt for (f, lvl), wt in w.items() if f == field}
        total += lv.map(weights).fillna(0.0).to_numpy()   # "missing" is not in the table: it adds 0
    prob = 2 ** total / (1 + 2 ** total)
    return total, prob


def surname_weights(values, m=0.95):
    """Match weight of agreeing on each surname, with m = 0.95 (an assumption) and u from its frequency."""
    last = prepared.customers()["last"]
    n = (last != "").sum()
    rows = []
    for v in values:
        k = int((last == v).sum())
        u = (k / n) ** 2 * n / max(n - 1, 1) if k else float("nan")
        rows.append({"surname": v, "records": k, "share": k / n, "u": u,
                     "weight": math.log2(m / u) if k else float("nan")})
    return pd.DataFrame(rows)


def train_pairs(vectors_df, dataset="customers"):
    """The candidate pairs of the training split with their true labels."""
    lab = evaluate.label_pairs(vectors_df, dataset)
    return lab[lab.split == "train"]
