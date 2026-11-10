import numpy as np
import pandas as pd

from larkfield_search import clicks, ltr
from larkfield_search.runs import get


def test_rerank_uses_recorded_scores():
    res = get("rerank-ce")("sofa", "T-007", 5)
    assert res[0][0] == "LK-10005"


def test_examine_and_simulate():
    assert clicks.examine(1) == 1.0 and abs(clicks.examine(4) - 0.25) < 1e-12
    c, a = clicks.simulate(["x", "y"], {"x": 2}, np.random.default_rng(0))
    assert len(c) == 2 and all(v in (0, 1) for v in c + a)


def test_click_labels_ipw():
    imp = pd.DataFrame({"query": ["q", "q"], "product_id": ["a", "b"], "position": [1, 4], "clicked": [1, 1]})
    lab = clicks.click_labels(imp, eta=1.0).set_index("product_id")
    assert lab.loc["a", "label"] == 1.0 and lab.loc["b", "label"] == 4.0


def test_ltr_trains_and_ranks():
    df, imp = ltr.train("judgments")
    assert set(ltr.FEATURES) <= set(df.columns) and len(imp) == len(ltr.FEATURES)
    assert get("ltr")("garden hose", "T-006", 5)
