"""route train: train TF-IDF + logistic regression on the training messages, choose its zone thresholds on
validation, and save it as a new version.

    route train --version v1
    route train --version v2 --extra data/launch_labels_sample.csv     add labelled launch-month messages
                                                                        (they can bring a new route)
"""

import pandas as pd

from larkroute import costs as cost_table
from larkroute import data, metrics, model_store, tfidf
from larkroute.methods import as_proba
from larkroute.zones import choose


def training_set(extra: str | None) -> pd.DataFrame:
    train = data.messages("train")[["message_id", "text", "route"]]
    if extra:
        lab = pd.read_csv(extra)
        if "split" in lab.columns:
            lab = lab[lab["split"] == "train"]
        texts = data.launch_month().set_index("message_id")["text"]
        lab = lab.assign(text=texts.loc[lab["message_id"]].to_numpy())[["message_id", "text", "route"]]
        train = pd.concat([train, lab], ignore_index=True)
    return train


def run(args):
    train = training_set(args.extra)
    val = data.messages("validation")
    model = tfidf.logistic_regression().fit(train["text"], train["route"])
    proba = as_proba(model.predict_proba(val["text"]), model.classes_).set_index(val.index)
    high, low, rep = choose(val, proba, cost_table.load(), args.review_max)
    row = metrics.score(args.version, val, proba.idxmax(axis=1))
    card = {"method": "TF-IDF (words and character n-grams) + logistic regression",
            "routes": list(model.classes_), "label_version": model_store.label_version(train),
            "training_messages": len(train), "thresholds": {"decide": high, "person_below": low},
            "validation": {"accuracy": row["accuracy"], "macro_f1": row["macro_f1"], **rep}}
    folder = model_store.save(args.version, model, card)
    if args.make_current:
        model_store.set_current(args.version)
    print(f"Saved {folder.relative_to(model_store.ROOT)}: {len(train)} messages, {len(model.classes_)} routes, "
          f"{card['label_version']}; validation accuracy {row['accuracy']:.3f}; decide at {high:.2f}, "
          f"person below {low:.2f}.{' Now the current model.' if args.make_current else ''}")


def add(sub):
    p = sub.add_parser("train", help="train and save a new model version")
    p.add_argument("--version", required=True)
    p.add_argument("--extra", help="a CSV of extra labelled launch-month messages (message_id, route, split)")
    p.add_argument("--review-max", type=float, default=0.10)
    p.add_argument("--make-current", action="store_true", help="the service loads this version from now on")
    p.set_defaults(func=run)
