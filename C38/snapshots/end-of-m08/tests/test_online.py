import numpy as np

from larkfield_search import bench, interleave


def test_team_draft_takes_turns():
    out, team = interleave.team_draft(["a", "b", "c"], ["b", "d", "e"], np.random.default_rng(0), n=4)
    assert len(out) == len(set(out)) == 4
    assert abs(team.count("A") - team.count("B")) <= 1


def test_significance_helpers():
    assert interleave.sign_test_p(50, 50) > 0.5
    assert interleave.sign_test_p(80, 20) < 0.001
    assert interleave.two_proportion_p(30, 100, 60, 100) < 0.001


def test_cost_per_1000():
    # 100 ms on one thread at 0.17 per hour for 4 vCPUs
    assert abs(bench.usd_per_1000(100, 1) - 1000 * 0.1 * 0.17 / 4 / 3600) < 1e-12
