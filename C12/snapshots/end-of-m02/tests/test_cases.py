import pytest

from adapt.cases import SPLITS, Case, load_cases, model_input, version


def test_the_evaluation_set_has_271_cases_in_three_splits():
    cases = load_cases(SPLITS)
    assert len(cases) == 271
    assert {s: sum(c.split == s for c in cases) for s in SPLITS} == {"dev": 102, "holdout": 98, "contaminated": 71}
    assert len(version()) == 12


def test_dev_is_the_default_and_an_unknown_split_is_refused():
    assert {c.split for c in load_cases()} == {"dev"}
    with pytest.raises(ValueError):
        load_cases(("test",))


def test_the_model_reads_the_attachment_name_too():
    case = Case("X", "dev", "normal", "en", "course", "plain", "", "photo.jpg", "", True, "H5", False)
    assert model_input(case) == "Attachment: photo.jpg"
