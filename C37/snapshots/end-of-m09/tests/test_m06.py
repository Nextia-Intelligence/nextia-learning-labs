import numpy as np

from larkfield_recs import data, registry


def test_content_can_suggest_new_products():
    shop = data.load()
    p = data.Period(shop, "launch")
    s = registry.make("content", p).fit().scores(p.users)
    new = np.flatnonzero(p.new_products)
    assert len(new) and np.isfinite(s[:, new]).any()


def test_new_slots_put_new_products_in_the_list():
    shop = data.load()
    p = data.Period(shop, "launch")
    recs = registry.make("als+new", p, {"slots": 2, "at": 4}).fit().recommend(p.users, 10)
    assert p.new_products[recs[:, 3]].all()


def test_hybrids_run():
    shop = data.load()
    p = data.Period(shop, "test")
    for name in ("hybrid-blend", "hybrid-switch"):
        assert registry.make(name, p).fit().recommend(p.users, 10).shape == (len(p.users), 10)
