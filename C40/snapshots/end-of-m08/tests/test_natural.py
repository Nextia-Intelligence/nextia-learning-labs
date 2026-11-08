"""Module 5: difference-in-differences, synthetic control, regression discontinuity, interrupted time series."""

import numpy as np

from larkfield_experiments import xp_cli
from larkfield_experiments.runs import load_run
from larkfield_experiments.synth import synth_weights


def test_did_with_all_provinces_is_close(make_run):
    make_run("regions")
    xp_cli.main(["did", "--control", "all"])
    a = load_run("regions").analysis()
    assert abs(a["estimate"] - 0.06) < 0.015


def test_synth_weights_are_a_mix():
    rng = np.random.default_rng(0)
    donors = rng.normal(size=(40, 4)).cumsum(axis=0)
    treated = donors @ np.array([0.5, 0.5, 0, 0])
    w = synth_weights(treated, donors)
    assert abs(w.sum() - 1) < 1e-9 and (w >= 0).all() and abs(w[0] - 0.5) < 0.05


def test_rdd_donut_removes_the_gamers(make_run):
    make_run("loyalty")
    xp_cli.main(["rdd"])
    plain = load_run("loyalty").analysis()["estimate"]
    xp_cli.main(["rdd", "--donut", "40"])
    donut = load_run("loyalty").analysis()["estimate"]
    assert abs(donut - 45) < abs(plain - 45)


def test_its_beats_the_naive_answer(make_run):
    make_run("launch")
    xp_cli.main(["its"])
    a = load_run("launch").analysis()
    assert a["low"] <= 0.02 <= a["high"]
