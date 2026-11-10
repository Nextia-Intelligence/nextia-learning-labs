"""Scale (Module 8, lesson 3): time and memory of each step on part of the records or on all of them.

The course data has 60,108 records. The lesson's 100,000 and 1 million record figures come from the course team's
runs on larger synthetic sets made by the same generator (they are in the lesson); this command measures the
same steps on what you have, so you can see how each step grows.
"""

import resource
import sys
import time

import numpy as np

from . import blocking, classifier, prepared, splinkmodel, vectors
from .runs import learned


def peak_mb():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3


def run(n, seed=1):
    """Time each step on n records chosen at random (every record when n >= all)."""
    df = prepared.customers()
    if n < len(df):
        df = df.iloc[np.sort(np.random.default_rng(seed).choice(len(df), n, replace=False))].reset_index(drop=True)
    out = {"records": len(df)}
    t0 = time.perf_counter()
    keys = blocking.customer_keys(df)
    cand = blocking.key_pairs(keys, ["postcode", "email", "phone", "surname4", "dob"])
    out["block_s"], out["candidates"] = time.perf_counter() - t0, len(cand)
    t0 = time.perf_counter()
    v = vectors.customer_vectors(cand, df)
    out["vectors_s"] = time.perf_counter() - t0
    try:
        model = learned.load("lgbm")
        t0 = time.perf_counter()
        classifier.predict(model, "lgbm", classifier.features(v))
        out["lgbm_s"] = time.perf_counter() - t0
    except FileNotFoundError:
        out["lgbm_s"] = None
    t0 = time.perf_counter()
    linker, _ = splinkmodel.train(df)
    out["splink_train_s"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    splinkmodel.predict(linker)
    out["splink_predict_s"] = time.perf_counter() - t0
    out["peak_mb"] = peak_mb()
    return out
