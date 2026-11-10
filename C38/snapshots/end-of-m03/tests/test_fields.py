from larkfield_search import rules
from larkfield_search.commands import explain
from larkfield_search.runs import get


def test_explain_parts_add_up():
    rows, total = explain.parts("garden hose", "LK-10003")
    assert abs(sum(r["part"] for r in rows) - total) < 1e-4
    assert [r["word"] for r in rows] == ["garden", "hose"]


def test_code_rule():
    assert rules.code_matches("LK-10012") == [("LK-10012", 1e6)]
    assert rules.code_matches("lk10012 rug") == [("LK-10012", 1e6)]
    assert rules.code_matches("10012")[0][0] == "LK-10012"
    assert rules.code_matches("99999") == []
    assert get("bm25-fields+codes")("lk 10012", None, 5)[0][0] == "LK-10012"


def test_title_weight_moves_title_matches_up():
    res = [p for p, _ in get("bm25-fields")("sofa", None, 5)]
    assert res[0] in ("LK-10005", "LK-10006")
