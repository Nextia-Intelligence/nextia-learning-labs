import numpy as np

from larkfield_recs import cli, data, registry
from larkfield_recs import rules as rules_mod


def test_rules_remove_what_they_should():
    shop = data.load()
    p = data.Period(shop, "test")
    long = np.tile(np.arange(48), (len(p.users), 1))
    out = rules_mod.apply(long, p, rules_mod.load(), 10)
    pr = shop.products
    shown = out[out >= 0]
    assert not pr.sensitive.to_numpy(dtype=bool)[shown].any()
    assert not pr.age_restricted.to_numpy(dtype=bool)[shown].any()
    assert pr.in_stock.to_numpy(dtype=bool)[shown].all()
    o = p.train[p.train.event == "order"]
    repeat = pr.repeat_days.to_numpy() > 0
    for u, row in zip(p.users, out):
        bought = set(o[(o.c == u) & ~repeat[o.p]].p)
        assert not bought & set(row.tolist())


def test_two_stage_trains_before_the_period():
    shop = data.load()
    p = data.Period(shop, "test")
    m = registry.make("two-stage", p, {"trees": 20, "negatives": 10, "train_days": 60}).fit()
    recs = m.recommend(p.users, 10)
    assert recs.shape == (len(p.users), 10)
    assert m.stage.p.start_day == p.start_day and m.importance


def test_session_and_llm_replay(capsys):
    cli.main(["session"])
    cli.main(["llm"])
    cli.main(["llm", "freeform"])
    out = capsys.readouterr().out
    assert "hit@10" in out and "content filter: 1" in out and "do not exist" in out
