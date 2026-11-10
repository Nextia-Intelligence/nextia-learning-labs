from larkfield_recs import cli, data, registry


def test_item_similarity_has_neighbours():
    shop = data.load()
    m = registry.make("item-cf", data.Period(shop, "test")).fit()
    assert m.sim.nnz > 0 and m.sim.diagonal().sum() == 0


def test_neighbour_methods_give_full_lists():
    shop = data.load()
    p = data.Period(shop, "test")
    for name in ("cooc", "lift", "item-cf", "user-user"):
        recs = registry.make(name, p).fit().recommend(p.users, 10)
        assert (recs >= 0).all()


def test_similar_and_explain(capsys):
    cli.main(["similar", "P10001", "--n", "3"])
    cli.main(["explain", "C100002"])
    out = capsys.readouterr().out
    assert "P10001" in out and "C100002" in out
