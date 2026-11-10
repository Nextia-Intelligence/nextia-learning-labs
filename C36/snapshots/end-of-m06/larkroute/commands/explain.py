"""route explain: why TF-IDF + logistic regression chose a route for one message: the words and letter groups
of the message with the largest weights for that route."""

import numpy as np

from larkroute import data, tfidf


def top_features(model, text: str, route: str, n: int = 8) -> list[tuple[str, float]]:
    feats, clf = model[0], model[-1]
    x = feats.transform([text])
    names = np.array([n.split("__", 1)[-1] for n in feats.get_feature_names_out()])
    k = list(clf.classes_).index(route)
    contrib = x.multiply(clf.coef_[k]).tocsr()
    idx = contrib.indices[np.argsort(-contrib.data)][:n]
    return [(str(names[i]), round(float(contrib[0, i]), 3)) for i in idx]


def run(args):
    train = data.messages("train")
    allm = data.messages()
    row = allm[allm["message_id"] == args.message_id]
    if row.empty:
        raise SystemExit(f"No message {args.message_id}")
    row = row.iloc[0]
    model = tfidf.logistic_regression().fit(train["text"], train["route"])
    proba = dict(zip(model.classes_, model.predict_proba([row["text"]])[0], strict=True))
    pred = max(proba, key=proba.get)
    print(f"{row['message_id']} ({row['language']}, {row['channel']}): {row['text']}")
    print(f"Label: {row['route']}. Model: {pred} ({proba[pred]:.2f}).")
    for route in dict.fromkeys([pred, row["route"]]):
        feats = ", ".join(f"'{f}' {w:+.2f}" for f, w in top_features(model, row["text"], route))
        print(f"Largest weights for {route}: {feats}")


def add(sub):
    p = sub.add_parser("explain", help="the words that made the TF-IDF model choose a route")
    p.add_argument("message_id")
    p.set_defaults(func=run)
