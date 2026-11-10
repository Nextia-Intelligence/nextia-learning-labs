from larkfield_recs import cli, data, harness


def test_matrix_is_sparse(capsys):
    shop = data.load()
    m = data.Period(shop, "test").matrix()
    assert m.shape == (80, 48) and m.nnz < 80 * 48
    cli.main(["matrix"])
    assert "filled cells" in capsys.readouterr().out


def test_random_split_contains_the_future():
    shop = data.load()
    p = data.Period(shop, "random")
    assert p.train.day.max() > p.start_day      # the leak: training events after the test period starts


def test_more_baselines():
    for m in ("trending", "popular-category"):
        _res, recs, _ = harness.run(m, "test")
        assert recs.shape[1] == 10 and (recs >= 0).all()


def test_leakage_command(capsys):
    cli.main(["leakage", "popular"])
    assert "random / time" in capsys.readouterr().out
