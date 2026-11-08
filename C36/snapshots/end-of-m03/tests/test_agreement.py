import pandas as pd

from larkroute.commands.agreement import agreement


def test_kappa_removes_the_agreement_that_comes_by_chance():
    df = pd.DataFrame({"label_chloe": ["a", "a", "b", "b"], "label_grace": ["a", "b", "a", "b"]})
    s = agreement(df)
    assert s["agreement"] == 0.5
    assert s["kappa"] == 0.0  # half the labels agree, as two coins would


def test_the_course_sample():
    from larkroute import data
    df = pd.read_csv(data.data_dir() / "double_labelled.csv")
    s = agreement(df)
    assert s["messages"] == 800
    assert 0.6 < s["kappa"] < s["agreement"] < 1
