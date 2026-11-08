"""A supervised pair classifier on the comparison vectors (Module 6, lesson 1).

Labels: the 3,000 labelled training pairs (labelled_pairs.csv), as a reviewer would label them. The model then
scores every candidate pair. Pairs are very unbalanced: about 1 candidate pair in 40 is a true pair.
"""

import numpy as np
import pandas as pd

from . import blocking, data, evaluate, torch_first, vectors

MODELS = ("logreg", "lgbm")


def features(v, dataset="customers"):
    """The model's inputs: every field similarity; for logistic regression, missing -> 0 plus a 'missing' flag."""
    return v[vectors.fields(dataset)].astype("float32")


def _flat(x):
    filled = x.fillna(0.0)
    flags = x.isna().astype("float32").add_suffix("_missing")
    return pd.concat([filled, flags], axis=1).to_numpy()


def make(kind, seed=1):
    torch_first()
    if kind == "logreg":
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
    from lightgbm import LGBMClassifier
    return LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=20,
                          random_state=seed, n_jobs=1, verbose=-1)


def fit(kind, x, y, seed=1):
    model = make(kind, seed)
    model.fit(_flat(x) if kind == "logreg" else x, np.asarray(y))
    return model


def predict(model, kind, x):
    return model.predict_proba(_flat(x) if kind == "logreg" else x)[:, 1]


def labelled_training_set(dataset="customers", extra=None, records=None):
    """Vectors and labels of the labelled pairs (customers: labelled_pairs.csv; products: training candidates).

    extra: more labelled pairs (record_id_l, record_id_r, label), for example from review (Module 8);
    records: the prepared table that has every record of those pairs (also the daily ones).
    """
    if dataset == "products":
        v = vectors.get(blocking.DEFAULT["products"])
        lab = evaluate.label_pairs(v, "products")
        lab = lab[lab.split == "train"]
        return features(lab, "products"), lab.same.to_numpy()
    lp = data.labelled_pairs()[["record_id_l", "record_id_r", "label"]]
    if extra is not None and len(extra):
        lp = pd.concat([lp, extra[["record_id_l", "record_id_r", "label"]]]).drop_duplicates(
            ["record_id_l", "record_id_r"], keep="last")
    lp = evaluate.ordered(lp)
    v = vectors.customer_vectors(lp[["record_id_l", "record_id_r"]].reset_index(drop=True), records)
    return features(v, dataset), lp.label.to_numpy()


def importance(model, kind, dataset="customers"):
    names = vectors.fields(dataset)
    if kind == "lgbm":
        gain = model.booster_.feature_importance("gain")
        return pd.Series(gain / gain.sum(), index=names).sort_values(ascending=False)
    coef = model[-1].coef_[0][: len(names)]
    return pd.Series(coef, index=names).sort_values(key=abs, ascending=False)
