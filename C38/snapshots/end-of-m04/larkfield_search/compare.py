"""Ranking measures and the comparison table of the Search and Ranking course.

The same file is in the course labs (compare.py) and in the project (larkfield_search/compare.py), so a notebook,
the `search` command and a case study compute every number the same way.

Judgments are grades: 2 = exact, 1 = partial, 0 = irrelevant. A product that has no judgment counts as 0.

- NDCG@k: gain 2**grade - 1 (exact 3, partial 1), discount log2(rank + 1); the ideal list is all judged
  products of the query, best first. A query with no exact or partial product has no NDCG (NaN).
- recall@k, precision@k and MRR count a product as relevant when its grade is 2 (exact). A query with no exact
  product has no recall and no MRR (NaN). MRR looks at the first 100 results.
- zero: the search returned nothing. judged@k: the share of the top k that has a judgment.
- Intervals: 95% bootstrap over queries (2,000 resamples, seed 0), on the mean and on paired differences.
"""

import math

import numpy as np
import pandas as pd

COLUMNS = ["method", "setting", "queries", "ndcg@10", "ndcg@10 95% CI", "recall@100", "mrr", "zero-result rate",
           "p50 ms", "p95 ms", "US$ per 1,000 queries"]
EXACT = 2


def gain(grade):
    return 2 ** grade - 1


def dcg(grades):
    return sum(gain(g) / math.log2(i + 2) for i, g in enumerate(grades))


def ndcg(ranked, judged, k=10):
    """NDCG@k of one ranked list of product IDs; `judged` is {product_id: grade}."""
    ideal = dcg(sorted(judged.values(), reverse=True)[:k])
    if ideal == 0:
        return float("nan")
    return dcg([judged.get(p, 0) for p in ranked[:k]]) / ideal


def recall(ranked, judged, k=100, min_grade=EXACT):
    relevant = {p for p, g in judged.items() if g >= min_grade}
    if not relevant:
        return float("nan")
    return len(relevant.intersection(ranked[:k])) / len(relevant)


def precision(ranked, judged, k=10, min_grade=EXACT):
    if not any(g >= min_grade for g in judged.values()):
        return float("nan")
    return sum(1 for p in ranked[:k] if judged.get(p, 0) >= min_grade) / k


def mrr(ranked, judged, k=100, min_grade=EXACT):
    if not any(g >= min_grade for g in judged.values()):
        return float("nan")
    for i, p in enumerate(ranked[:k]):
        if judged.get(p, 0) >= min_grade:
            return 1.0 / (i + 1)
    return 0.0


def judged_at(ranked, judged, k=10):
    top = ranked[:k]
    return float("nan") if not top else sum(1 for p in top if p in judged) / len(top)


def per_query(run, judgments):
    """One row per query of `run` ({query_id: [product_id, ...]}) with every measure."""
    rows = []
    for qid, ranked in run.items():
        judged = judgments.get(qid, {})
        ranked = list(ranked)
        rows.append({"query_id": qid, "ndcg@10": ndcg(ranked, judged, 10), "ndcg@5": ndcg(ranked, judged, 5),
                     "recall@100": recall(ranked, judged, 100), "recall@10": recall(ranked, judged, 10),
                     "precision@5": precision(ranked, judged, 5), "mrr": mrr(ranked, judged),
                     "zero": float(len(ranked) == 0), "judged@10": judged_at(ranked, judged, 10)})
    return pd.DataFrame(rows).set_index("query_id")


def bootstrap(values, n=2000, seed=0):
    """(mean, low, high): the mean of the values and its 95% bootstrap interval (NaN values are left out)."""
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), (n, len(v)))].mean(axis=1)
    return float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired(a, b, measure="ndcg@10", n=2000, seed=0):
    """B minus A on the queries that both have: mean difference, its 95% interval, and queries better/worse/same."""
    d = (b[measure] - a[measure]).dropna()
    mean, low, high = bootstrap(d.to_numpy(), n, seed)
    return {"queries": len(d), "difference": mean, "low": low, "high": high,
            "better": int((d > 1e-9).sum()), "worse": int((d < -1e-9).sum()), "same": int((d.abs() <= 1e-9).sum())}


def summary(pq):
    """The table row of one run's per-query measures."""
    m, lo, hi = bootstrap(pq["ndcg@10"].to_numpy())
    return {"queries": len(pq), "ndcg@10": m, "ndcg@10 low": lo, "ndcg@10 high": hi,
            "recall@100": float(pq["recall@100"].mean()), "mrr": float(pq["mrr"].mean()),
            "zero-result rate": float(pq["zero"].mean()), "judged@10": float(pq["judged@10"].mean())}


def by_slice(pq, queries, column, measure="ndcg@10"):
    """Mean and 95% interval of a measure for each value of a query column (for example band or language)."""
    joined = pq.join(queries.set_index("query_id")[[column]], how="left")
    rows = []
    for value, part in joined.groupby(column, dropna=False):
        m, lo, hi = bootstrap(part[measure].to_numpy())
        rows.append({column: value, "queries": len(part), measure: m, "low": lo, "high": hi,
                     "zero-result rate": float(part["zero"].mean())})
    return pd.DataFrame(rows)


def latency(ms):
    """p50 and p95 of a list of milliseconds."""
    a = np.asarray(ms, dtype=float)
    return (float(np.percentile(a, 50)), float(np.percentile(a, 95))) if len(a) else (float("nan"),) * 2


def cost_per_1000(p50_ms, usd_per_hour, threads=1):
    """US$ per 1,000 queries on a server that runs `threads` queries at once at p50 milliseconds each."""
    seconds = 1000 * p50_ms / 1000 / threads
    return usd_per_hour * seconds / 3600


class Table:
    """The comparison table: add one row per run, print it, or get it as a DataFrame."""

    def __init__(self):
        self.rows = []

    def add(self, method, setting, pq, ms=None, usd_per_hour=None):
        s = summary(pq)
        p50, p95 = latency(ms) if ms is not None else (float("nan"), float("nan"))
        cost = cost_per_1000(p50, usd_per_hour) if usd_per_hour and ms is not None else float("nan")
        self.rows.append({"method": method, "setting": setting, "queries": s["queries"], "ndcg@10": s["ndcg@10"],
                          "ndcg@10 95% CI": f"{s['ndcg@10 low']:.3f}-{s['ndcg@10 high']:.3f}",
                          "recall@100": s["recall@100"], "mrr": s["mrr"], "zero-result rate": s["zero-result rate"],
                          "p50 ms": p50, "p95 ms": p95, "US$ per 1,000 queries": cost})
        return self.rows[-1]

    def frame(self):
        return pd.DataFrame(self.rows, columns=COLUMNS)

    def __str__(self):
        return self.frame().to_string(index=False, float_format=lambda x: f"{x:.3f}")
