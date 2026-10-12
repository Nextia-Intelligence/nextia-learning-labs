"""The held-out questions: reserved once, stratified, and protected by their lock."""

import json
import shutil
from pathlib import Path

import pytest

from scripts import holdout

EVAL = Path(__file__).resolve().parent.parent / "evaluation"


def test_the_committed_heldout_set_matches_its_lock():
    assert holdout.check().startswith("Held-out set: 41 questions (bramble 14, larkfield 27)")


def test_no_question_is_in_both_sets_and_none_is_lost():
    held, dev, bank = (holdout.load(EVAL / f) for f in ("heldout.jsonl", "dev.jsonl", "questions.jsonl"))
    assert not {q["id"] for q in held} & {q["id"] for q in dev}
    assert {q["id"] for q in held} | {q["id"] for q in dev} == {q["id"] for q in bank}


def test_the_split_is_stratified_and_repeatable():
    bank = holdout.load(EVAL / "questions.jsonl")
    held, dev = holdout.split(bank, 27, 0.4)
    assert [q["id"] for q in held] == [q["id"] for q in holdout.load(EVAL / "heldout.jsonl")]
    for key in {(q["tenant"], q["kind"]) for q in bank}:
        n = sum((q["tenant"], q["kind"]) == key for q in bank)
        if n >= 2:   # every kind of every shop is in both sets
            assert any((q["tenant"], q["kind"]) == key for q in held) and any((q["tenant"], q["kind"]) == key for q in dev)


def test_a_changed_heldout_file_is_refused(tmp_path):
    for f in ("heldout.jsonl", "heldout.lock"):
        shutil.copy(EVAL / f, tmp_path / f)
    q = holdout.load(tmp_path / "heldout.jsonl")
    q[0]["keys"] = [".*"]   # "fixing" a key after seeing a result
    (tmp_path / "heldout.jsonl").write_text("".join(json.dumps(x) + "\n" for x in q))
    with pytest.raises(SystemExit, match="changed after it was reserved"):
        holdout.check(tmp_path)
