import numpy as np

from larkfield_search import dense
from larkfield_search.runs import get
from larkfield_search.runs.dense import rrf


def test_rrf_by_hand():
    out = dict(rrf([["a", "b"], ["b", "c"]], k_rrf=60))
    assert abs(out["b"] - (1 / 62 + 1 / 61)) < 1e-12
    assert next(iter(dict(rrf([["a", "b"], ["b", "c"]])))) == "b"


def test_dense_uses_shipped_query_vectors():
    s = dense.scores("garden hose", "T-006")
    assert s.shape == (12,) and np.argmax(s) == 2  # LK-10003 is row 2


def test_hybrid_runs():
    for name in ("dense", "hybrid-rrf", "hybrid-blend"):
        res = get(name)("garden hose", "T-006", 5)
        assert res[0][0] == "LK-10003"
