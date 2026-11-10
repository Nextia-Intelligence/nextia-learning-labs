"""Module 6: adjustment for confounders and refutation tests."""

from larkfield_experiments import xp_cli
from larkfield_experiments.runs import load_run


def test_adjustment_is_closer_than_the_naive_answer(make_run):
    make_run("logs")
    xp_cli.main(["adjust"])
    a = load_run("logs").analysis()
    truth = load_run("logs").truth()
    for r in a["results"]:
        t = truth[r["target"].lower()]["effect"]
        assert abs(r["estimate"] - t) < abs(a["naive"] - t) / 2


def test_weighting_balances_the_confounders(make_run):
    make_run("logs", customers=20_000)
    xp_cli.main(["adjust"])
    a = load_run("logs").analysis()
    assert max(abs(v) for v in a["balance_after"].values()) < 0.05


def test_placebo_refuter_gives_about_zero(make_run):
    make_run("logs", customers=10_000)
    xp_cli.main(["refute", "--simulations", "5"])
    a = load_run("logs").analysis()
    assert abs(a["refuters"]["placebo_treatment_refuter"]["new_effect"]) < abs(a["estimate"]) / 2
