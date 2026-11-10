"""Module 7: uplift curves and models."""

import numpy as np

from larkfield_experiments import xp_cli
from larkfield_experiments.runs import load_run
from larkfield_experiments.uplift import qini_coefficient, uplift_curve


def test_a_perfect_score_beats_a_random_one():
    rng = np.random.default_rng(0)
    n = 20_000
    t = rng.integers(0, 2, n)
    lift = rng.random(n) < 0.3
    y = (rng.random(n) < 0.05 + 0.10 * lift * t).astype(float)
    q_good = qini_coefficient(*uplift_curve(lift + rng.random(n) * 0.1, y, t))
    q_rand = qini_coefficient(*uplift_curve(rng.random(n), y, t))
    assert q_good > q_rand + 50


def test_t_learner_beats_random_targeting(make_run, capsys):
    make_run("email")
    xp_cli.main(["uplift", "--learner", "t", "--budget", "10000"])
    xp_cli.main(["check"])
    out = capsys.readouterr().out
    mine = float(out.split("Your 10,000 customers: ")[1].split()[0])
    rand = float(out.split("Random 10,000: ")[1].split(".")[0])
    assert mine > 3 * rand
    assert "for a budget" not in out
    assert load_run("email").analysis()["qini"] > 0
