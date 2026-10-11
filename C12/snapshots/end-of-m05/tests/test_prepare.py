import json

from adapt.prepare import ROOT, find_secret, overlap, prepare, shingles


def test_a_secret_is_a_password_with_a_digit_or_symbol_not_the_word_password():
    assert find_secret("It keeps saying my password is wrong.") == ""
    assert find_secret("My password is Rose2026! and it fails") == "password"
    assert find_secret("card 4111 1111 1111 1111 was charged") == "card number"
    assert find_secret("write to me at ana@example.com") == "email address"


def test_near_copies_overlap_even_when_a_number_changes():
    a = shingles("I can't log in to my account and the reset email never came. Order LK-837201.")
    b = shingles("I can't log in to my account and the reset email never came. Order LK-837202.")
    assert overlap(a, b) >= 0.4


def test_the_exercise_records_are_caught(tmp_path):
    m = prepare(extra=ROOT / "data/exercise/extra_records.jsonl", out=tmp_path)
    reasons = {r["id"]: r["reason"] for r in m["rejected_rows"] if r["id"].startswith("X-")}
    assert reasons == {"X-001": "evaluation leak", "X-002": "secret", "X-003": "duplicate"}


def test_the_prepared_data_is_the_same_every_time(tmp_path):
    m = prepare(out=tmp_path)
    saved = json.loads((ROOT / "data/prepared/manifest.json").read_text(encoding="utf-8"))
    assert m["train"]["sha256_12"] == saved["train"]["sha256_12"]
    assert m["rejected"] == {"duplicate": 23, "evaluation leak": 1, "known wrong label": 70}
    assert (m["train"]["records"], m["val"]["records"]) == (900, 100)
    assert m["uncovered"] == ["French", "H2", "H3", "H4", "H5"]


def test_validation_and_training_share_no_ticket_and_no_evaluation_case(tmp_path):
    prepare(out=tmp_path)
    ids = {p: {json.loads(x)["id"] for x in (tmp_path / f"{p}.jsonl").read_text().splitlines()}
           for p in ("train", "val")}
    cases = {json.loads(x)["case_id"] for x in (ROOT / "data/eval/cases.jsonl").read_text().splitlines()}
    assert not ids["train"] & ids["val"] and not (ids["train"] | ids["val"]) & cases
