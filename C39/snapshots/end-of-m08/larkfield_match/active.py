"""Active learning: label the pairs the model is least sure about (Module 6, lesson 2).

The pool is every training candidate pair; the "reviewer" is the true answer (as if Ivana labelled each pair
correctly). Each round trains logistic regression on the labels so far, then asks for the `batch` pool pairs
whose probability is closest to 0.5. The comparison: the same number of labels chosen at random.
"""

import numpy as np

from . import blocking, classifier, evaluate, thresholds, vectors


def simulate(rounds=12, start=20, batch=40, strategy="uncertain", seed=1, kind="logreg"):
    """F1 on the test pairs after each round: returns (labels, F1 with the best validation threshold, F1 at 0.5).

    The first F1 chooses the threshold on the validation pairs, so it uses their labels too; the second uses
    only the labels of the rounds (threshold 0.5)."""
    rng = np.random.default_rng(seed)
    v = evaluate.label_pairs(vectors.get(blocking.DEFAULT["customers"]))
    x_all = classifier.features(v)
    pool = np.where(v.split.to_numpy() == "train")[0]
    y = v.same.to_numpy()
    # start: half from pairs that share an email or phone (likely true), half at random, so both classes exist
    likely = pool[(v.email_eq.to_numpy()[pool] == 1) | (v.phone_eq.to_numpy()[pool] == 1)]
    labelled = list(rng.choice(likely, start // 2, replace=False)) + list(rng.choice(pool, start // 2, replace=False))
    out = []
    for r in range(rounds + 1):
        idx = np.array(sorted(set(labelled)))
        model = classifier.fit(kind, x_all.iloc[idx], y[idx], seed=seed)
        p = classifier.predict(model, kind, x_all)
        scored = v[["record_id_l", "record_id_r"]].assign(score=p)
        t = thresholds.best_f1(scored, "customers")
        m = evaluate.pair_measures(thresholds.decide(scored, t), "customers", "test")
        m05 = evaluate.pair_measures(thresholds.decide(scored, 0.5), "customers", "test")
        out.append((len(idx), m["f1"], m05["f1"]))
        if r == rounds:
            break
        free = np.setdiff1d(pool, idx)
        if strategy == "uncertain":
            pick = free[np.argsort(np.abs(p[free] - 0.5))[:batch]]
        else:
            pick = rng.choice(free, batch, replace=False)
        labelled += list(pick)
    return out
