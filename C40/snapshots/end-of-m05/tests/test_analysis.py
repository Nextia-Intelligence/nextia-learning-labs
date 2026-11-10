"""Module 3: CUPED, the bootstrap and the sample ratio check."""

import numpy as np

from larkfield_experiments import xp_cli
from larkfield_experiments.commands.analyse import estimate
from larkfield_experiments.cuped import cuped_adjust
from larkfield_experiments.runs import load_run


def test_cuped_keeps_the_mean_and_cuts_the_variance():
    rng = np.random.default_rng(1)
    x = rng.normal(10, 3, 5000)
    y = 2 * x + rng.normal(0, 3, 5000)
    adj, theta = cuped_adjust(y, x)
    assert abs(adj.mean() - y.mean()) < 1e-9 and abs(theta - 2) < 0.1 and adj.var() < y.var() / 3


def test_cuped_and_bootstrap_on_a_test(make_run):
    make_run("delivery", customers=30_000)
    df = load_run("delivery").table("customers")
    plain, cuped, boot = estimate(df, "revenue"), estimate(df, "revenue", cuped=True), estimate(df, "revenue", bootstrap=300)
    assert cuped["high"] - cuped["low"] < plain["high"] - plain["low"]
    assert abs((boot["high"] - boot["low"]) / (plain["high"] - plain["low"]) - 1) < 0.2


def test_srm_found_in_the_planted_run_only(make_run, capsys):
    make_run("srm", customers=60_000)
    xp_cli.main(["srm", "srm"])
    assert "SAMPLE RATIO MISMATCH" in capsys.readouterr().out
    make_run("aa", customers=60_000)
    xp_cli.main(["srm", "aa"])
    assert "no mismatch" in capsys.readouterr().out
