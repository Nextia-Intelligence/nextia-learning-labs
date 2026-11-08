"""`vision probe`: a logistic regression on embeddings (a linear probe), with all or a few labels per class."""
import numpy as np

from larkvision import data as D
from larkvision.commands.compare import add_row
from larkvision.compare import classification_row, classification_scores
from larkvision.embeddings import MODELS, load, matrix
from larkvision.paths import data_dir


def register(sub):
    p = sub.add_parser("probe", help="a linear probe on embeddings")
    p.add_argument("--embeddings", choices=sorted(MODELS), default="clip")
    p.add_argument("--per-class", type=int, default=0, help="labelled photos per class (0 = all)")
    p.add_argument("--balanced", action="store_true", help="give every class the same total weight")
    p.add_argument("--seed", type=int, default=0)
    p.set_defaults(run=run)


def probe(emb, train, test, per_class=0, balanced=False, seed=0):
    from sklearn.linear_model import LogisticRegression
    y = np.array([r["label"] for r in train])
    idx = np.arange(len(train))
    if per_class:
        rng = np.random.default_rng(seed)
        idx = np.concatenate([rng.permutation(np.where(y == k)[0])[:per_class] for k in sorted(set(y))])
    X = matrix(emb, [train[i]["image_id"] for i in idx])
    clf = LogisticRegression(C=2.0, max_iter=5000, class_weight="balanced" if balanced else None).fit(X, y[idx])
    return clf.predict(matrix(emb, [r["image_id"] for r in test])), len(idx)


def run(args):
    d = data_dir(args.data)
    emb = load(d, args.embeddings)
    train, test = D.catalogue(d, "train"), D.catalogue(d, "test")
    pred, n = probe(emb, train, test, args.per_class, args.balanced, args.seed)
    y = [r["label"] for r in test]
    s = classification_scores(y, list(pred), D.CLASSES)
    how = f"{args.per_class} per class" if args.per_class else "all labels"
    if args.balanced:
        how += ", balanced classes"
    print(f"{MODELS[args.embeddings]} + logistic regression ({how}, {n} labelled photos): accuracy {s['accuracy']:.3f};"
          f" worst class {s['worst_class']} (recall {s['worst_recall']:.2f})")
    add_row(classification_row(f"{args.embeddings} probe ({how})", y, list(pred), "catalogue test", None, None, n,
                               "see the model card"))
