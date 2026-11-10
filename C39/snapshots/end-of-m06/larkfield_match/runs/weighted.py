"""A second baseline: field similarities times weights chosen by hand (Module 4, lesson 3)."""

import numpy as np

from .. import blocking, thresholds, vectors

# Our choice, before looking at any result: strong identifiers count most, the town least.
WEIGHTS = {"email_eq": 3.0, "phone_eq": 2.5, "dob_eq": 2.5, "postcode_eq": 2.0, "last_jw": 2.0, "first_jw": 1.5,
           "street_tsr": 1.5, "number_eq": 1.0, "town_eq": 0.5}
PRODUCT_WEIGHTS = {"title_tsr": 3.0, "gtin_eq": 3.0, "size_ratio": 2.0, "pack_eq": 2.0, "brand_eq": 1.0,
                   "price_ratio": 0.5}


def weighted_score(v, weights):
    """Sum of weight x similarity; a missing value adds nothing."""
    total = np.zeros(len(v), dtype="float64")
    for f, w in weights.items():
        total += w * np.nan_to_num(v[f].to_numpy(dtype="float64"), nan=0.0)
    return total


def _run(dataset, weights):
    v = vectors.get(blocking.DEFAULT[dataset])
    scored = v[["record_id_l", "record_id_r"]].assign(score=weighted_score(v, weights))
    t = thresholds.best_f1(scored, dataset)
    return thresholds.decide(scored, t)


RUNS = {
    "weighted": ("customers", lambda: _run("customers", WEIGHTS),
                 "hand weights on the field similarities; threshold: best F1 on validation"),
    "p-weighted": ("products", lambda: _run("products", PRODUCT_WEIGHTS),
                   "hand weights on the title, size, pack, barcode and brand; threshold: best F1 on validation"),
}
