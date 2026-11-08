"""Learning to rank (Module 6, lessons 3 and 4): features for each candidate and LambdaMART with LightGBM.

The candidates of a query are the top 100 of `hybrid-rrf`. Each candidate gets the features below. LightGBM's
`lambdarank` learns how to order the candidates of a query from labels: the judgments (2 exact, 1 partial,
0 irrelevant) of the training queries, or labels made from the clicks in the synthetic query log.
"""

import json
from functools import lru_cache

import numpy as np
import pandas as pd

from . import clicks, data, dense, index, spell
from .detect import detect
from .paths import outputs_dir
from .rules import code_matches

FEATURES = ["bm25_title", "bm25_description", "bm25_category", "bm25_attributes", "bm25_title_fr", "dense",
            "rrf", "hybrid_rank", "class_match", "price_log", "in_stock", "on_sale", "rating", "rating_count_log",
            "clicks_log", "carts_log", "age_days", "query_words", "query_has_number"]
DEPTH = 100
LOG_END = pd.Timestamp("2025-10-26")
PARAMS = {"objective": "lambdarank", "n_estimators": 300, "learning_rate": 0.05, "num_leaves": 31,
          "min_child_samples": 20, "subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.8,
          "label_gain": [0, 1, 3], "random_state": 0, "n_jobs": 1, "verbose": -1}


@lru_cache(maxsize=1)
def product_table():
    """Product features that do not depend on the query (popularity from the synthetic log)."""
    cat = data.catalogue()
    imp = data.impressions()
    c = imp.groupby("product_id")[["clicked", "added_to_cart"]].sum()
    t = pd.DataFrame({
        "price_log": np.log1p(cat["price"].to_numpy()),
        "in_stock": cat["in_stock"].astype(float).to_numpy(),
        "on_sale": cat["on_sale"].astype(float).to_numpy(),
        "rating": pd.to_numeric(cat["average_rating"], errors="coerce").fillna(0).to_numpy(),
        "rating_count_log": np.log1p(cat["rating_count"].to_numpy()),
        "clicks_log": np.log1p(cat["product_id"].map(c["clicked"]).fillna(0).to_numpy()),
        "carts_log": np.log1p(cat["product_id"].map(c["added_to_cart"]).fillna(0).to_numpy()),
        "age_days": (LOG_END - pd.to_datetime(cat["added"])).dt.days.clip(lower=0).to_numpy(),
    }, index=cat["product_id"])
    return t


def candidates(query, query_id=None, depth=DEPTH):
    """The top `depth` candidates of hybrid-rrf with every feature, in hybrid order."""
    from .runs.dense import hybrid_rrf
    cand = hybrid_rrf(query, query_id, depth)
    ids = [p for p, _ in cand]
    cat = data.catalogue()
    row = pd.Series(np.arange(len(cat)), index=cat["product_id"])[ids].to_numpy()
    q = spell.correct(query)[0]
    f = pd.DataFrame({"product_id": ids})
    for field in ("title", "description", "category", "attributes"):
        f[f"bm25_{field}"] = index.scores(q, field, "norm")[row]
    f["bm25_title_fr"] = index.scores(q, "title_fr", "norm_fr")[row]
    f["dense"] = dense.scores(query, query_id)[row]
    f["rrf"] = [s for _, s in cand]
    f["hybrid_rank"] = np.arange(1, len(ids) + 1)
    classes = detect(query)["classes"]
    f["class_match"] = cat["product_class"].to_numpy()[row].astype(object)
    f["class_match"] = f["class_match"].isin(classes).astype(float)
    pt = product_table().loc[ids].reset_index(drop=True)
    f = pd.concat([f, pt], axis=1)
    f["query_words"] = len(query.split())
    f["query_has_number"] = float(any(ch.isdigit() for ch in query))
    return f


def click_grades(qids, eta=None):
    """{(query_id, product_id): label} from the log for the given queries: 1 if the product was ever clicked when
    shown for that query (naive), or with eta, 2/1/0 from the click rate divided by examine(position)."""
    s = data.searches()
    s = s[s["query_id"].isin(set(qids))]
    imp = data.impressions().merge(s[["search_id", "query_id"]], on="search_id")
    imp = imp.rename(columns={"query_id": "query"})
    lab = clicks.click_labels(imp, eta)
    if eta is None:
        lab["grade"] = (lab["clicks"] > 0).astype(int)
    else:
        lab["grade"] = np.where(lab["label"] >= 0.5, 2, np.where(lab["label"] > 0, 1, 0))
    return {(q, p): g for q, p, g in zip(lab["query"], lab["product_id"], lab["grade"])}


def training_set(labels="judgments", split="train"):
    qs = data.split(split)
    if labels == "judgments":
        j = data.judgments()
        grade = lambda qid, pid: j.get(qid, {}).get(pid, 0)
    else:
        cg = click_grades(qs["query_id"], eta=clicks.ETA if labels == "clicks-ipw" else None)
        grade = lambda qid, pid: cg.get((qid, pid), 0)
    parts = []
    for qid, text in zip(qs["query_id"], qs["query"]):
        f = candidates(text, qid)
        f["label"] = [grade(qid, p) for p in f["product_id"]]
        f["query_id"] = qid
        parts.append(f)
    return pd.concat(parts, ignore_index=True)


def model_path(labels):
    return outputs_dir() / f"ltr-{labels}.txt"


def train(labels="judgments", split="train"):
    from . import torch_first
    torch_first()
    import lightgbm as lgb
    df = training_set(labels, split)
    groups = df.groupby("query_id", sort=False).size().to_numpy()
    m = lgb.LGBMRanker(**PARAMS)
    m.fit(df[FEATURES], df["label"], group=groups)
    m.booster_.save_model(str(model_path(labels)))
    imp = dict(zip(FEATURES, m.booster_.feature_importance("gain").round(1).tolist()))
    (outputs_dir() / f"ltr-{labels}.json").write_text(json.dumps({"rows": len(df), "queries": len(groups),
                                                                  "positives": int((df["label"] > 0).sum()),
                                                                  "importance_gain": imp}, indent=1))
    booster.cache_clear()
    return df, imp


@lru_cache(maxsize=4)
def booster(labels):
    from . import torch_first
    torch_first()
    import lightgbm as lgb
    if not model_path(labels).exists():
        train(labels)
    return lgb.Booster(model_file=str(model_path(labels)))


def rank(query, query_id=None, labels="judgments", k=100):
    f = candidates(query, query_id)
    if f.empty:
        return []
    f["score"] = booster(labels).predict(f[FEATURES])
    f = f.sort_values(["score", "product_id"], ascending=[False, True])
    first = code_matches(query)
    taken = {p for p, _ in first}
    return (first + [(p, float(s)) for p, s in zip(f["product_id"], f["score"]) if p not in taken])[:k]

