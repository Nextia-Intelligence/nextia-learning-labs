import pytest

from doc_extract import documents


def test_get_by_id_or_file_name():
    d = documents.get("D011")
    assert documents.get(d.file).doc_id == "D011"
    assert d.path.exists()


def test_unknown_document_stops_with_a_message():
    with pytest.raises(SystemExit):
        documents.get("D999")


def test_receipts_include_the_claim():
    r = documents.receipts()
    assert len(r) == 54
    assert any(d.kind == "claim" for d in r)


def test_show_writes_one_picture_per_page(capsys):
    from doc_extract import show

    show.main(["D058"])
    out = capsys.readouterr().out
    assert "page 2" in out
