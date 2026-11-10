"""Measure a matcher against the true entities.

A pair is two records. A true pair is two records of the same entity. Pair precision is the share of the pairs a
matcher calls "same" that are true pairs; pair recall is the share of the true pairs that it finds.

Splits: every entity is in train, validation or test. A pair belongs to the test split when one of its records
belongs to a test entity (so a test record wrongly joined to a training record counts as a test error); to
validation when one record is in validation and none in test; else to train.
"""

import pandas as pd

from . import data

RANK = {"train": 0, "validation": 1, "test": 2}


def ordered(df, l_col="record_id_l", r_col="record_id_r"):
    """The same pairs with the smaller record ID first, one row per pair."""
    lo = df[[l_col, r_col]].min(axis=1)
    hi = df[[l_col, r_col]].max(axis=1)
    out = df.assign(**{l_col: lo, r_col: hi})
    return out[out[l_col] != out[r_col]].drop_duplicates([l_col, r_col])


def true_pairs(dataset="customers"):
    """Every pair of records that belong to the same entity (record_id_l < record_id_r) and its split."""
    t = data.dataset_truth(dataset)
    m = t.merge(t, on="entity_id", suffixes=("_l", "_r"))
    m = m[m.record_id_l < m.record_id_r]
    return m[["record_id_l", "record_id_r", "entity_id", "split_l"]].rename(columns={"split_l": "split"})


def pair_split(df, dataset="customers"):
    """The split of each pair (see the module notes)."""
    rank = data.dataset_truth(dataset).set_index("record_id").split.map(RANK)
    r = pd.concat([df.record_id_l.map(rank), df.record_id_r.map(rank)], axis=1).max(axis=1)
    return r.map({v: k for k, v in RANK.items()})


def label_pairs(df, dataset="customers"):
    """Adds `same` (1 when both records belong to one entity) and `split` to a pairs table."""
    ent = data.dataset_truth(dataset).set_index("record_id").entity_id
    return df.assign(same=(df.record_id_l.map(ent) == df.record_id_r.map(ent)).astype(int),
                     split=pair_split(df, dataset))


def pair_measures(pairs, dataset="customers", split="test"):
    """Pair precision, recall and F1 of the pairs with match == 1, on one split ('all' for every split)."""
    pred = ordered(pairs[pairs["match"] == 1])
    pred = label_pairs(pred, dataset)
    truth = true_pairs(dataset)
    if split != "all":
        pred = pred[pred.split == split]
        truth = truth[truth.split == split]
    tp = int(pred.same.sum())
    fp = len(pred) - tp
    fn = len(truth) - tp
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": p, "recall": r, "f1": f1, "tp": tp, "fp": fp, "fn": fn,
            "predicted": len(pred), "true": len(truth)}


def by_group(pairs, dataset, split, group):
    """Recall of the true pairs and precision of the predicted pairs, per group.

    group 'source': the two sources of the pair (for example garden-shop);
    group 'problem': the practice problem of one of the records (planted.csv), or 'none'.
    """
    pred = label_pairs(ordered(pairs[pairs["match"] == 1]), dataset)
    truth = true_pairs(dataset)
    if split != "all":
        pred, truth = pred[pred.split == split], truth[truth.split == split]
    found = set(zip(pred.record_id_l, pred.record_id_r))
    truth = truth.assign(found=[(a, b) in found for a, b in zip(truth.record_id_l, truth.record_id_r)])
    keyf = _group_key(dataset, group)
    rows = []
    t_key = truth.apply(lambda x: keyf(x.record_id_l, x.record_id_r), axis=1) if len(truth) else pd.Series(dtype=str)
    p_key = pred.apply(lambda x: keyf(x.record_id_l, x.record_id_r), axis=1) if len(pred) else pd.Series(dtype=str)
    for k in sorted(set(t_key) | set(p_key)):
        tk, pk = truth[t_key == k], pred[p_key == k]
        rows.append({group: k, "true": len(tk), "found": int(tk.found.sum()),
                     "recall": tk.found.mean() if len(tk) else float("nan"),
                     "predicted": len(pk), "precision": pk.same.mean() if len(pk) else float("nan")})
    return pd.DataFrame(rows)


def _group_key(dataset, group):
    if group == "source":
        def src(rid):
            return {"S": "shop", "L": "loyalty", "G": "garden", "N": "feed_a", "C": "feed_b"}.get(rid[0], "?")
        return lambda a, b: "-".join(sorted((src(a), src(b))))
    if group == "problem":
        pl = data.product_planted() if dataset == "products" else data.planted()
        order = ["placeholder_phone", "brothers", "family_email", "saint_town", "pack_of_2", "moved"]
        probs = pl.groupby("record_id").problem.apply(lambda s: min(s, key=order.index)).to_dict()

        def key(a, b):
            ks = [probs[x] for x in (a, b) if x in probs]
            return min(ks, key=order.index) if ks else "none"
        return key
    raise SystemExit(f"Unknown group {group!r}: use source or problem.")


def entity_count(pairs, record_ids):
    """How many entities the pairs make (connected components, records with no pair count as one each)."""
    from .cluster import components
    return components(pairs, record_ids).cluster_id.nunique()


def true_entity_count(dataset="customers"):
    return data.dataset_truth(dataset).entity_id.nunique()
