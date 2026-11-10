from larkfield_search import detect, normalise, spell, synonyms
from larkfield_search.runs import get


def test_fold_and_units():
    assert normalise.fold("Café 24”x18") == "cafe 24 inch x 18"
    assert normalise.norm("Grey Outdoor Cushions 18''") == ["grey", "outdoor", "cushion", "18", "inch"]
    assert normalise.norm_fr("Coussins gris") == ["coussin", "gris"]


def test_spell():
    assert spell.correct_word("cushon") == ("cushion", "corrected")
    assert spell.correct_word("sofa") == ("sofa", "known")
    assert spell.correct("outdor cushion")[1] == [("outdor", "outdoor")]


def test_synonyms_two_way_and_one_way():
    assert synonyms.expansion("couch") == "sofa"
    assert synonyms.expansion("modern sofa") == "couch"
    assert synonyms.expansion("sectional") == "sofa"
    assert synonyms.expansion("sofa", only="sectional => sofa") == ""
    assert synonyms.matches("light blue pillow", "light, lamp")


def test_detect_price_and_colour():
    d = detect.detect("grey cushion under 50 dollars")
    assert d["price_max"] == 50 and d["colours"] == ["grey"] and "under" not in d["clean"]


def test_runs_of_module_4():
    for name in ("bm25-norm", "bm25-norm+spell", "bm25-norm+spell+syn", "llm-rewrite", "bm25-norm+spell+syn+detect"):
        assert get(name)("outdor cushion", None, 5)
    assert get("llm-rewrite")("coussin gris", "T-008", 3)[0][0] in ("LK-10001", "LK-10011")
