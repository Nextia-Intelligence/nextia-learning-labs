import math

import pandas as pd

from larkfield_search import compare


def test_ndcg_by_hand():
    judged = {"a": 2, "b": 1, "c": 0}
    # ranked b, a: dcg = 1/log2(2) + 3/log2(3); ideal a, b: 3 + 1/log2(3)
    got = compare.ndcg(["b", "a"], judged, 10)
    want = (1 + 3 / math.log2(3)) / (3 + 1 / math.log2(3))
    assert abs(got - want) < 1e-12
    assert compare.ndcg(["a", "b"], judged) == 1.0
    assert math.isnan(compare.ndcg(["a"], {"a": 0}))


def test_recall_precision_mrr():
    judged = {"a": 2, "b": 2, "c": 1}
    assert compare.recall(["x", "a", "c"], judged, 100) == 0.5
    assert compare.precision(["x", "a", "b", "c", "y"], judged, 5) == 0.4
    assert compare.mrr(["x", "c", "b"], judged) == 1 / 3
    assert compare.mrr(["x"], judged) == 0.0


def test_per_query_and_zero():
    pq = compare.per_query({"q1": ["a"], "q2": []}, {"q1": {"a": 2}, "q2": {"b": 2}})
    assert pq.loc["q1", "ndcg@10"] == 1.0
    assert pq.loc["q2", "zero"] == 1.0
    assert compare.summary(pq)["zero-result rate"] == 0.5


def test_bootstrap_and_paired():
    m, lo, hi = compare.bootstrap([0.0, 1.0] * 50)
    assert m == 0.5 and lo < 0.5 < hi
    a = pd.DataFrame({"ndcg@10": [0.1, 0.2, 0.3]}, index=["x", "y", "z"])
    b = pd.DataFrame({"ndcg@10": [0.2, 0.2, 0.5]}, index=["x", "y", "z"])
    d = compare.paired(a, b)
    assert d["better"] == 2 and d["same"] == 1 and abs(d["difference"] - 0.1) < 1e-9


def test_table_and_cost():
    t = compare.Table()
    pq = compare.per_query({"q1": ["a"]}, {"q1": {"a": 2}})
    row = t.add("bm25", "default", pq, ms=[10, 20, 30], usd_per_hour=3.6)
    assert row["p50 ms"] == 20 and abs(row["US$ per 1,000 queries"] - 0.02) < 1e-9
    assert "bm25" in str(t)
