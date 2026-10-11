import hashlib

from adapt.answer import SYSTEM_PROMPT, parse_answer
from adapt.records import ROOT, load_source, sources, to_record


def test_every_example_has_the_same_three_messages():
    record = to_record(load_source()[0])
    assert [m["role"] for m in record["messages"]] == ["system", "user", "assistant"]
    assert record["messages"][0]["content"] == SYSTEM_PROMPT
    assert parse_answer(record["messages"][2]["content"])[0] == {"team": "payment", "needs_human": False}


def test_every_data_file_matches_its_recorded_source():
    for name, s in sources().items():
        assert hashlib.sha256((ROOT / s["file"]).read_bytes()).hexdigest() == s["sha256"], name
    assert sources()["evaluation"]["permitted_use"].startswith("EVALUATION ONLY")


def test_89_training_tickets_need_a_person_and_each_label_says_how_it_was_made():
    rows = load_source()
    assert len(rows) == 4696
    assert sum(r["needs_human"] for r in rows) == 89
    assert {r["label_how"].split(":")[0] for r in rows} == {"read", "not read"}
