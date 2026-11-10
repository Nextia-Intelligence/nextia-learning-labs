"""Learned matching: pair classifiers trained on labelled pairs (Module 6, lesson 1)."""

import pickle

from .. import blocking, classifier, thresholds, vectors
from ..paths import out


def scores(kind, dataset="customers", extra=None, records=None, name=None, save=True):
    """Train on the labelled pairs, keep the model (outputs/models/<name>.pkl), and score every candidate pair."""
    x, y = classifier.labelled_training_set(dataset, extra, records)
    model = classifier.fit(kind, x, y)
    name = name or f"{'p-' if dataset == 'products' else ''}{kind}"
    if save:
        with open(out("models", f"{name}.pkl"), "wb") as f:
            pickle.dump(model, f)
    v = vectors.get(blocking.DEFAULT[dataset])
    p = classifier.predict(model, kind, classifier.features(v, dataset))
    return v[["record_id_l", "record_id_r"]].assign(score=p)


def _run(kind, dataset="customers"):
    s = scores(kind, dataset)
    return thresholds.decide(s, thresholds.best_f1(s, dataset))


def load(name):
    with open(out("models", f"{name}.pkl"), "rb") as f:
        return pickle.load(f)


RUNS = {
    "logreg": ("customers", lambda: _run("logreg"), ("logistic regression on the comparison vector, 3,000 labelled "
               "pairs; best F1 threshold on validation")),
    "lgbm": ("customers", lambda: _run("lgbm"), ("LightGBM on the comparison vector, 3,000 labelled pairs; best F1 "
             "threshold on validation")),
    "p-lgbm": ("products", lambda: _run("lgbm", "products"), ("LightGBM on the product comparison vector, training "
               "candidate pairs; best F1 threshold on validation")),
}

