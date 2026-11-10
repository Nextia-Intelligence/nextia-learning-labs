import numpy as np

from larkfield_recs import beyond, cli, data, harness


def test_beyond_accuracy_measures():
    shop = data.load()
    p = data.Period(shop, "test")
    same = np.tile(np.arange(10), (len(p.users), 1))
    b = beyond.measures(same, p)
    assert 0 <= b["diversity"] <= 1 and b["novelty"] > 0


def test_segments_cover_every_customer():
    res, _, p = harness.run("popular", "test")
    assert sum(v["customers"] for v in res["segments"].values()) == len(p.users)


def test_compare_uses_the_same_customers(capsys):
    harness.run("popular", "test")
    harness.run("random", "test")
    cli.main(["compare", "random", "popular", "--by", "segment"])
    out = capsys.readouterr().out
    assert "difference" in out and "95% interval" in out
