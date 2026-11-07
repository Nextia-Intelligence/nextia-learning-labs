"""`vision baseline`: train a classical method on the catalogue and add it to your comparison table."""
import time
from pathlib import Path

import numpy as np

from larkvision import data as D
from larkvision.commands.compare import add_row
from larkvision.compare import classification_row, classification_scores
from larkvision.features import colour_histogram, hog_features
from larkvision.paths import data_dir


def register(sub):
    p = sub.add_parser("baseline", help="a colour histogram or HOG baseline on the catalogue")
    p.add_argument("--method", choices=["histogram", "hog"], default="histogram")
    p.add_argument("--k", type=int, default=5, help="neighbours for the histogram method")
    p.set_defaults(run=run)


def fit_predict(method, train, sets, k=5):
    from sklearn.linear_model import LogisticRegression
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    fn = colour_histogram if method == "histogram" else hog_features
    Xtr = np.stack([fn(r["path"]) for r in train])
    y = [r["label"] for r in train]
    if method == "histogram":
        model = KNeighborsClassifier(k, n_jobs=1).fit(Xtr, y)
    else:
        model = make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=3000)).fit(Xtr, y)
    out = {}
    for name, rows in sets.items():
        t0 = time.perf_counter()
        X = np.stack([fn(r["path"]) for r in rows])
        pred = model.predict(X)
        out[name] = (pred, 1000 * (time.perf_counter() - t0) / len(rows))
    return out


def run(args):
    d = data_dir(args.data)
    for_paths = lambda rows: [dict(r, path=str(Path(d) / r["file"])) for r in rows]  # noqa: E731
    train = for_paths(D.catalogue(d, "train"))
    sets = {"catalogue test": for_paths(D.catalogue(d, "test")), "new studio": for_paths(D.new_studio(d))}
    res = fit_predict(args.method, train, sets, args.k)
    name = f"colour histogram + {args.k}-NN" if args.method == "histogram" else "HOG + logistic regression"
    for setting, (pred, ms) in res.items():
        y = [r["label"] for r in sets[setting]]
        s = classification_scores(y, list(pred), D.CLASSES)
        print(f"{name}, {setting}: accuracy {s['accuracy']:.3f}; worst class {s['worst_class']} "
              f"(recall {s['worst_recall']:.2f}); {ms:.1f} ms per photo")
        add_row(classification_row(name, y, list(pred), setting, round(ms, 2), 0, len(train), "none (our code)"))
    print("Added to outputs/table.json. See it with: vision compare --task catalogue")
