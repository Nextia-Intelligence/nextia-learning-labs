"""`vision labels`: find training photos whose label looks wrong (cross-validated probabilities on embeddings)."""
from pathlib import Path

import numpy as np

from larkvision import data as D
from larkvision.compare import reveal
from larkvision.embeddings import MODELS, load, matrix
from larkvision.paths import data_dir


def register(sub):
    p = sub.add_parser("labels", help="find training photos with a suspect label")
    p.add_argument("--embeddings", choices=sorted(MODELS), default="dinov2")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--score", action="store_true", help="compare with the planted label errors (the sealed key)")
    p.set_defaults(run=run)


def suspects(emb, train, folds=5):
    """Rank training photos by the probability that the model gives to their own label (lowest first)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict
    classes = sorted({r["label"] for r in train})
    y = np.array([classes.index(r["label"]) for r in train])
    X = matrix(emb, [r["image_id"] for r in train])
    P = cross_val_predict(LogisticRegression(C=2.0, max_iter=5000), X, y, cv=folds, method="predict_proba", n_jobs=1)
    own = P[np.arange(len(y)), y]
    order = np.argsort(own, kind="mergesort")
    return [(train[i]["image_id"], train[i]["label"], classes[P[i].argmax()], float(own[i])) for i in order
            if P[i].argmax() != y[i]]


def run(args):
    d = data_dir(args.data)
    train = D.catalogue(d, "train")
    found = suspects(load(d, args.embeddings), train)
    print(f"{len(found)} training photos where the model prefers another label. The first {args.top}:")
    for iid, given, sug, p in found[:args.top]:
        print(f"  {iid}  labelled {given:9s}  the model says {sug:9s}  (probability of the label {p:.2f})")
    if args.score:
        key = reveal(Path(d) / "sealed-key.txt")
        planted = {e["image_id"] for e in key["label_errors"]}
        top = {f[0] for f in found[:args.top]}
        print(f"Planted label errors in your top {args.top}: {len(planted & top)} of {len(planted)}")
