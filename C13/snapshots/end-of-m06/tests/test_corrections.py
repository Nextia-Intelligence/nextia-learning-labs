import sqlite3

import pytest

from doc_extract import compare, corrections, documents


@pytest.fixture
def db(tmp_path):
    d = documents.get("D011")
    con = corrections.connect(str(tmp_path / "review.db"))
    corrections.store(con, d.doc_id, compare.run(d, "text"))
    return con


def test_a_correction_keeps_the_original(db):
    v = corrections.correct(db, "D011", "total", "999.99", "Grace", "typed from the paper receipt")
    assert v == 1
    cur = corrections.current(db, "D011")
    assert cur["total"]["value"] == "999.99" and "Grace" in cur["total"]["source"]
    kinds = [h[0] for h in corrections.history(db, "D011") if h[1] == "total"]
    assert kinds == ["extracted", "corrected"]
    extracted = db.execute("SELECT value FROM extractions WHERE doc_id='D011' AND field='total'").fetchone()[0]
    assert extracted == documents.get("D011").fields["total"]


def test_nothing_can_be_overwritten(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE extractions SET value = 'x' WHERE doc_id = 'D011'")
    corrections.correct(db, "D011", "date", "2026-01-01", "Grace", "test")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("UPDATE corrections SET new_value = 'y'")


def test_a_correction_needs_a_note_and_a_known_field(db):
    with pytest.raises(ValueError):
        corrections.correct(db, "D011", "total", "1.00", "Grace", " ")
    with pytest.raises(ValueError):
        corrections.correct(db, "D011", "colour", "red", "Grace", "why not")


def test_versions_count_up(db):
    corrections.correct(db, "D011", "total", "1.00", "Grace", "first")
    assert corrections.correct(db, "D011", "total", "2.00", "Priya", "second") == 2
