"""Module 4: peeking, sequential tests, many metrics, interference."""

import json

import numpy as np

from larkfield_experiments import xp_cli
from larkfield_experiments.commands.metrics import benjamini_hochberg, bonferroni
from larkfield_experiments.sequential import sequential_path


def test_sequential_test_rarely_finds_a_false_winner():
    rng = np.random.default_rng(0)
    false = 0
    for _ in range(300):
        x = rng.normal(0, 1, (2, 2000)).cumsum(axis=1)
        n = np.arange(1, 2001)
        d, v = (x[1] - x[0]) / n, 2 / n
        path = sequential_path(d[49::50], v[49::50], tau2=0.01)
        false += min(p for _, _, p in path) < 0.05
    assert false / 300 < 0.05


def test_peeking_finds_more_false_winners(capsys):
    xp_cli.main(["peek", "--aa-tests", "400"])
    lines = {line.split(":")[0].strip(): float(line.split(":")[1].split("%")[0]) for line in
             capsys.readouterr().out.splitlines()[1:]}
    assert lines["peeking every day, stop at p < 0.05"] > 2 * lines[f"fixed length, one look at day {28}"]
    assert lines["sequential test, look every day"] < 6


def test_corrections():
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    assert bonferroni(p).sum() == 1
    assert benjamini_hochberg(p).sum() == 2


def test_shared_stock_inflates_the_test(make_run):
    folder = make_run("stock", customers=60_000)
    truth = json.loads((folder / "truth.json").read_text())
    import pandas as pd
    c = pd.read_csv(folder / "customers.csv")
    diff = c[c.variant == "B"].revenue.mean() - c[c.variant == "A"].revenue.mean()
    assert diff > truth["revenue"]["effect"]
