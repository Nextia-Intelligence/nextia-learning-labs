import json

import numpy as np

from larkfield_recs import cli, data, registry
from larkfield_recs.paths import outputs_dir


def test_als_and_bpr_are_repeatable():
    shop = data.load()
    p = data.Period(shop, "test")
    for name in ("als", "bpr"):
        a = registry.make(name, p, {"factors": 4, "iterations": 3}).fit().recommend(p.users, 5)
        b = registry.make(name, p, {"factors": 4, "iterations": 3}).fit().recommend(p.users, 5)
        assert np.array_equal(a, b)


def test_new_customers_get_the_trending_list():
    shop = data.load()
    p = data.Period(shop, "test")
    m = registry.make("als", p, {"factors": 4}).fit()
    unknown = np.flatnonzero(~m.known)
    if len(unknown):
        assert (m.recommend(unknown[:1], 5)[0] == m.fallback[:5]).all()


def test_tune_uses_validation_only(capsys):
    cli.main(["tune", "als", "--grid", "factors=4,8", "--grid", "iterations=2"])
    best = json.loads((outputs_dir() / "best-als.json").read_text())
    assert best["factors"] in (4, 8)
    assert "validation" in capsys.readouterr().out
