"""Probabilistic linkage: Fellegi–Sunter weights from labels, and Splink without labels (Module 5)."""

from .. import blocking, evaluate, fs, splinkmodel, thresholds, vectors


def fs_labels():
    """m and u counted on the training candidate pairs (labels known), then the total weight of every pair."""
    v = vectors.get(blocking.DEFAULT["customers"])
    tr = fs.train_pairs(v)
    table = fs.estimate(tr, tr.same)
    prior = tr.same.mean()
    _, prob = fs.score(v, table, prior)
    scored = v[["record_id_l", "record_id_r"]].assign(score=prob)
    return thresholds.decide(scored, thresholds.best_f1(scored, "customers"))


def splink_scores():
    """Splink's match weight for every candidate pair of the default blocking (-30 when Splink gave a match
    probability below 0.001, so the pair is not in its output)."""
    if splinkmodel.model_path().exists():
        linker = splinkmodel.load()
    else:
        linker, _ = splinkmodel.train()
        splinkmodel.save(linker)
    pred = splinkmodel.predict(linker)[["record_id_l", "record_id_r", "match_weight", "match_probability"]]
    pred = evaluate.ordered(pred)
    cand = blocking.candidates(blocking.DEFAULT["customers"])
    s = cand.merge(pred, on=["record_id_l", "record_id_r"], how="left").fillna(
        {"match_weight": -30.0, "match_probability": 0.0})
    return s.rename(columns={"match_weight": "score"})


def splink_run():
    scored = splink_scores()
    return thresholds.decide(scored, thresholds.best_f1(scored, "customers"))


RUNS = {
    "fs-labels": ("customers", fs_labels, ("Fellegi–Sunter weights counted on labelled training pairs; best F1 "
                  "threshold on validation")),
    "splink": ("customers", splink_run, ("Splink on DuckDB, weights learned without labels; score = match weight; "
               "best F1 threshold on validation")),
}
