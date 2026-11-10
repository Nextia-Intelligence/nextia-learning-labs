import itertools

from larkfield_search import index


def test_build_and_fts_and_or():
    meta = index.build_all()
    assert meta["products"] == 12
    assert next(p for p, _ in index.fts_search("garden hose", 10, "and")) == "LK-10003"
    assert index.fts_search("garden zebra", 10, "and") == []
    assert len(index.fts_search("garden zebra", 10, "or")) >= 1


def test_bm25_scores_and_top():
    s = index.scores("garden hose")
    top = index.top(s, 3)
    assert top[0][0] == "LK-10003"
    assert all(a[1] >= b[1] for a, b in itertools.pairwise(top))
    assert index.top(index.scores("zebra"), 3) == []


def test_bm25_lucene_formula():
    # one word, check against the formula of index.py
    import math

    import numpy as np

    from larkfield_search import data
    r = index.lengths("all")
    n, avg = len(r), float(r.mean())
    s = index.scores("hose")
    df = int(np.count_nonzero(s))
    row = int(np.flatnonzero(data.catalogue()["product_id"].to_numpy() == "LK-10004")[0])
    tf = 1  # "hose reel keeps your water pipe tidy"
    want = math.log(1 + (n - df + 0.5) / (df + 0.5)) * tf / (tf + index.K1 * (1 - index.B + index.B * r[row] / avg))
    assert abs(float(s[row]) - want) < 1e-5
