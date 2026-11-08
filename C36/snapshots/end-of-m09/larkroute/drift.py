"""Drift: watch what the router does week by week (route shares, confidence, the review and person zones), and
group the unsure messages to find a topic that has no route."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from larkroute.methods import as_proba


def route_messages(model, card, messages: pd.DataFrame) -> pd.DataFrame:
    p = as_proba(model.predict_proba(messages["text"]), model.classes_).set_index(messages.index)
    conf, best = p.max(axis=1), p.idxmax(axis=1)
    th = card["thresholds"]
    zone = np.where((best == "needs_person") | (conf < th["person_below"]), "person",
                    np.where(conf >= th["decide"], "decide", "review"))
    return messages.assign(predicted=best, confidence=conf.round(4), zone=zone)


def psi(expected: pd.Series, actual: pd.Series, floor: float = 1e-4) -> float:
    """Population stability index of two sets of shares (the same categories)."""
    cats = sorted(set(expected.index) | set(actual.index))
    e = expected.reindex(cats, fill_value=0).clip(lower=floor)
    a = actual.reindex(cats, fill_value=0).clip(lower=floor)
    return float(((a - e) * np.log(a / e)).sum())


def weekly(routed: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    ref_share = reference["predicted"].value_counts(normalize=True)
    weeks = pd.to_datetime(routed["created_at"]).dt.to_period("W-SUN").dt.start_time.dt.date
    rows = []
    for week, g in routed.groupby(weeks):
        share = g["predicted"].value_counts(normalize=True)
        rows.append({"week": str(week), "messages": len(g), "delivery": round(share.get("delivery", 0), 3),
                     "product": round(share.get("product", 0), 3), "account": round(share.get("account", 0), 3),
                     "mean_conf": round(g["confidence"].mean(), 3),
                     "unsure": round((g["zone"] != "decide").mean(), 3), "psi": round(psi(ref_share, share), 3)})
    return pd.DataFrame(rows)


def topics(texts: pd.Series, k: int = 6, seed: int = 36) -> tuple[pd.DataFrame, np.ndarray]:
    """Group messages by their words (k-means on TF-IDF) and show each group's size and top words."""
    vec = TfidfVectorizer(min_df=3, max_df=0.5, stop_words="english", sublinear_tf=True)
    x = vec.fit_transform(texts)
    km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(x)
    words = np.array(vec.get_feature_names_out())
    rows = []
    for c in range(k):
        top = words[np.argsort(km.cluster_centers_[c])[::-1][:6]]
        rows.append({"group": c, "messages": int((km.labels_ == c).sum()), "top_words": ", ".join(top)})
    return pd.DataFrame(rows).sort_values("messages", ascending=False), km.labels_
