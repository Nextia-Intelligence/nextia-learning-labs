"""Run a search run on many queries, time it, and measure it."""

import time

from . import compare, data, runs


def run_queries(name, qs, k=100):
    """({query_id: [product_id]}, [milliseconds]) for the queries in the DataFrame qs."""
    fn = runs.get(name)
    out, ms = {}, []
    for qid, text in zip(qs["query_id"], qs["query"]):
        t0 = time.perf_counter()
        res = fn(text, qid, k)
        ms.append((time.perf_counter() - t0) * 1000)
        out[qid] = [p for p, _ in res]
    return out, ms


def evaluate(name, split="test", k=100):
    """(per-query measures, milliseconds) of a run on one split."""
    qs = data.split(split)
    ranked, ms = run_queries(name, qs, k)
    return compare.per_query(ranked, data.judgments()), ms
