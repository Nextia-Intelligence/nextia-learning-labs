from larkroute.commands.compare import QUICK, compare


def test_quick_compare_runs_and_the_model_beats_people_on_cost():
    rows = {r["method"]: r for r in compare(QUICK, quiet=True)}
    assert set(rows) == set(QUICK)
    assert rows["everything to a person"]["accuracy"] == 0
    assert rows["TF-IDF + logistic regression"]["accuracy"] > 0.8
    assert rows["TF-IDF + logistic regression"]["total_per_1000"] < rows["everything to a person"]["total_per_1000"]
