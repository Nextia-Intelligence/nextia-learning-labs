from larkfield_search import judge, runs
from larkfield_search.cli import main


def test_kappa_known_values():
    assert judge.kappa([0, 1, 2, 2], [0, 1, 2, 2]) == 1.0
    # agreement 0.5 with both judges at 50/50 on two labels: kappa 0
    assert abs(judge.kappa([0, 0, 2, 2], [0, 2, 0, 2], labels=(0, 2))) < 1e-12


def test_agreement_table():
    r = judge.agreement([2, 1, 0, 0], [2, 0, 0, 0])
    assert r["pairs"] == 4 and r["agreement"] == 0.75
    assert r["table"].loc["partial", "irrelevant"] == 1


def test_sample_and_llm(capsys):
    df = judge.sample(runs.get("bm25"), n_queries=1, per_query=3)
    assert list(df.columns)[-1] == "your_grade" and len(df) <= 3
    main(["judge", "llm"])
    assert "agreement 67%" in capsys.readouterr().out


def test_compare_command(capsys):
    main(["compare", "current", "bm25", "--split", "test", "--by", "source"])
    out = capsys.readouterr().out
    assert "bm25 minus current on 4 test queries" in out and "translated" in out
