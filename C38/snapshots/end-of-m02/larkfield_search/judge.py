"""Relevance judgments: samples to judge, and agreement between two judges (Module 2)."""

import json

import numpy as np
import pandas as pd

from . import data
from .paths import data_dir

NAMES = {2: "exact", 1: "partial", 0: "irrelevant"}


def sample(run_fn, n_queries=3, per_query=10, seed=1, split="validation"):
    """A table to judge: the top results of a run for a few validation queries (English WANDS queries)."""
    q = data.split(split)
    q = q[q["source"] == "wands"].reset_index(drop=True)
    rng = np.random.default_rng(seed)
    cat = data.catalogue().set_index("product_id")
    rows = []
    for i in sorted(rng.choice(len(q), n_queries, replace=False)):
        qid, text = q.loc[i, "query_id"], q.loc[i, "query"]
        for pid, _ in run_fn(text, qid, per_query)[:per_query]:
            r = cat.loc[pid]
            rows.append({"query_id": qid, "query": text, "product_id": pid, "title": r["title"],
                         "product_class": r["product_class"], "description": r["description"][:300],
                         "attributes": r["attributes"][:200], "your_grade": ""})
    return pd.DataFrame(rows)


def kappa(a, b, labels=(0, 1, 2), weighted=False):
    """Cohen's kappa between two lists of grades (linear weights when weighted=True)."""
    a, b = np.asarray(a, int), np.asarray(b, int)
    k = len(labels)
    m = np.zeros((k, k))
    for x, y in zip(a, b):
        m[labels.index(x), labels.index(y)] += 1
    m /= m.sum()
    w = (np.abs(np.subtract.outer(np.arange(k), np.arange(k))) / (k - 1) if weighted
         else 1 - np.eye(k))
    expected = np.outer(m.sum(1), m.sum(0))
    return 1 - (w * m).sum() / (w * expected).sum()


def agreement(a, b):
    """Raw agreement, Cohen's kappa, weighted kappa and the confusion table (rows a, columns b)."""
    a, b = list(map(int, a)), list(map(int, b))
    table = pd.crosstab(pd.Series([NAMES[x] for x in a], name="judge A"),
                        pd.Series([NAMES[x] for x in b], name="judge B"))
    order = [NAMES[g] for g in (2, 1, 0)]
    table = table.reindex(index=order, columns=order, fill_value=0)
    return {"pairs": len(a), "agreement": float(np.mean(np.array(a) == np.array(b))), "kappa": float(kappa(a, b)),
            "weighted kappa": float(kappa(a, b, weighted=True)), "table": table}


def llm_judgments():
    """The recorded labels of a language model (chat-small) for judged and unjudged pairs."""
    rows = [json.loads(x) for x in (data_dir() / "recorded" / "llm_judgments.jsonl").read_text().splitlines()]
    return pd.DataFrame(rows)
