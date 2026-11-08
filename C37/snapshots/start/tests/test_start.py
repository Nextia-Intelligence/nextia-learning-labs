import json

import numpy as np

from larkfield_recs import cli, data, harness, metrics
from larkfield_recs.paths import data_dir


def test_load_maps_ids_to_numbers():
    shop = data.load()
    assert shop.n_products == 48 and shop.n_customers == 80
    assert shop.events.p.notna().all() and shop.events.c.notna().all()


def test_metrics_by_hand():
    rec, truth = np.array([3, 1, 7, 9, 5]), [1, 5, 8]
    assert metrics.precision_at_k(rec, truth, 5) == 2 / 5
    assert metrics.recall_at_k(rec, truth, 5) == 2 / 3
    assert metrics.hit_at_k(rec, truth, 5) == 1.0
    assert abs(metrics.average_precision_at_k(rec, truth, 5) - (1 / 2 + 2 / 5) / 3) < 1e-12
    dcg = 1 / np.log2(3) + 1 / np.log2(6)
    ideal = 1 + 1 / np.log2(3) + 1 / np.log2(4)
    assert abs(metrics.ndcg_at_k(rec, truth, 5) - dcg / ideal) < 1e-12


def test_bootstrap_interval_contains_mean():
    mean, lo, hi = metrics.bootstrap(np.r_[np.zeros(50), np.ones(50)])
    assert lo < mean < hi and mean == 0.5


def test_time_split_has_no_future():
    shop = data.load()
    p = data.Period(shop, "test")
    assert p.train.day.max() < p.start_day
    assert len(p.users) == len(p.truth) > 0


def test_popular_is_the_same_for_everyone():
    res, recs, _ = harness.run("popular", "test")
    assert (recs == recs[0]).all()
    assert 0 <= res["recall"] <= 1 and res["coverage"] < 0.5


def test_evaluate_and_info_print(capsys):
    cli.main(["evaluate", "popular", "--quick"])
    out = capsys.readouterr().out
    assert "recall@10" in out and "coverage" in out
    cli.main(["info"])
    assert "Products: 48" in capsys.readouterr().out


def test_check_and_reset(capsys):
    res, _, _ = harness.run("popular", "validation", quick=True)
    (data_dir() / "expected.json").write_text(json.dumps({"popular_validation_quick_recall10": res["recall"]}))
    cli.main(["check"])
    assert "Setup check passed." in capsys.readouterr().out
    cli.main(["reset"])
    assert "all files are right" in capsys.readouterr().out
