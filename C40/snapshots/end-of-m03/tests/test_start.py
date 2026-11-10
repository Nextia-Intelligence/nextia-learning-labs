"""The simulator, the basic analysis and the commands of Module 1."""

import json

import numpy as np
from scipy import stats

from larkfield_experiments import sim_cli, xp_cli
from larkfield_experiments.ab import ab_run, no_effect
from larkfield_experiments.stats import diff_means, diff_ratio


def test_no_change_means_no_true_effect():
    _, truth, _ = ab_run(1, 5_000, 7, no_effect)
    assert truth["revenue"]["effect"] == 0 and truth["orders"]["effect"] == 0


def test_same_seed_same_data():
    a, _, _ = ab_run(3, 3_000, 7, no_effect)
    b, _, _ = ab_run(3, 3_000, 7, no_effect)
    assert a["customers"].equals(b["customers"])


def test_welch_matches_scipy():
    rng = np.random.default_rng(0)
    a, b = rng.normal(0, 1, 500), rng.normal(0.2, 2, 700)
    r = diff_means(a, b)
    assert abs(r["p"] - stats.ttest_ind(b, a, equal_var=False).pvalue) < 1e-9
    assert r["low"] < r["difference"] < r["high"]


def test_ratio_metric_is_ratio_of_sums():
    r = diff_ratio([1, 0, 1], [2, 1, 1], [1, 1, 1], [1, 1, 2])
    assert abs(r["mean_a"] - 2 / 4) < 1e-12 and abs(r["mean_b"] - 3 / 4) < 1e-12


def test_setup_check_email_interval_contains_truth(make_run, capsys):
    make_run("email")
    xp_cli.main(["analyse"])
    xp_cli.main(["check"])
    out = capsys.readouterr().out
    assert "the interval contains the true effect" in out


def test_launch_naive_answer_is_far_from_truth(make_run, capsys):
    folder = make_run("launch")
    truth = json.loads((folder / "truth.json").read_text())
    assert 0.07 < truth["naive_before_after"]["change"] < 0.09
    assert abs(truth["true_effect_after"]["relative"] - 0.02) < 0.005
    xp_cli.main(["naive"])
    assert "+8." in capsys.readouterr().out


def test_users_spend_more_than_the_block_causes(make_run):
    folder = make_run("logs", customers=8_000)
    truth = json.loads((folder / "truth.json").read_text())
    assert truth["naive"]["difference"] > 2 * truth["att"]["effect"] > 0


def test_sim_list_and_run(capsys, runs_in_tmp):
    sim_cli.main(["list"])
    assert "email" in capsys.readouterr().out
    sim_cli.main(["run", "--scenario", "email", "--customers", "2000", "--seed", "5"])
    assert (runs_in_tmp / "runs" / "email-s5" / "truth.json").exists()


def test_reset_deletes_runs(make_run, runs_in_tmp):
    make_run("email", customers=1_000)
    xp_cli.main(["reset", "--yes"])
    assert not (runs_in_tmp / "runs").exists()


def test_check_follows_the_analysed_run(make_run, capsys):
    make_run("email", customers=3_000)
    xp_cli.main(["analyse"])
    make_run("logs", customers=3_000)
    xp_cli.main(["check"])
    assert "Run email-s40: the last analysis was `xp analyse`." in capsys.readouterr().out


def test_check_without_truth_says_so(make_run, capsys):
    folder = make_run("logs", customers=3_000)
    xp_cli.main(["naive"])
    (folder / "truth.json").write_text("{}\n")
    try:
        xp_cli.main(["check"])
    except SystemExit as e:
        assert str(e).startswith("No truth for this run")
    else:
        raise AssertionError("xp check should stop when the run has no truth")
