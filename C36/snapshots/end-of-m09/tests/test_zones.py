import pandas as pd

from larkroute import costs
from larkroute.zones import choose, decide, reliability, report


def test_reliability_of_a_tiny_example():
    table, ece = reliability([0.95, 0.95, 0.55, 0.55], [True, False, True, True], bins=10)
    assert list(table["messages"]) == [2, 2]
    assert ece == round(0.5 * abs(0.55 - 1.0) + 0.5 * abs(0.95 - 0.5), 4)


def test_three_zones(tiny):
    p = pd.DataFrame({"delivery": [0.95, 0.6, 0.2, 0.1], "billing": [0.05, 0.4, 0.3, 0.9]}, index=tiny.index)
    p["account"] = [0, 0, 0.5, 0]
    z = decide(p, high=0.9, low=0.55)
    assert list(z) == ["delivery", "review", "needs_person", "billing"]
    r = report(tiny, z, costs.load())
    assert r["decide"] == 0.5 and r["review"] == 0.25 and r["person"] == 0.25


def test_choose_keeps_the_review_load_under_the_limit(tiny):
    p = pd.DataFrame({"delivery": [0.95, 0.6, 0.2, 0.1], "billing": [0.05, 0.4, 0.8, 0.9]}, index=tiny.index)
    high, low, rep = choose(tiny, p, costs.load(), review_max=0.25)
    assert rep["review"] + rep["person"] <= 0.25
