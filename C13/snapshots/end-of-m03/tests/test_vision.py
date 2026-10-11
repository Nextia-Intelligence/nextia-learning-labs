import json

from doc_extract import documents, vision


def test_every_receipt_page_has_a_recorded_answer_for_both_prompts():
    for d in documents.receipts():
        page = d.truth.get("receipt_page", 1)
        assert vision.recorded(d.file, page, "v2"), d.file
        assert vision.recorded(d.file, page, "v1"), d.file


def test_a_v2_answer_becomes_the_same_record_as_the_other_paths():
    d = documents.get("D036")
    ex = vision.read(d.file)
    assert ex.path == "vision"
    assert set(ex.fields) == set(vision.FIELD_NAMES)
    assert ex.value("total") == d.fields["total"]
    assert ex.fields["total"].confidence is not None
    assert ex.usage["tokens_in"] > 1000


def test_empty_answers_count_as_absent_and_bad_json_is_noted():
    rec = {"file": "x.jpg", "page": 1, "answer": json.dumps({"order_number": "N/A", "total": 12.5})}
    ex = vision.to_extraction(rec)
    assert ex.value("order_number") is None and ex.value("total") == "12.5"
    bad = vision.to_extraction({"file": "x.jpg", "page": 1, "answer": "not json"})
    assert "not valid JSON" in bad.notes[0]


def test_the_v2_request_has_a_strict_schema_and_the_picture():
    body = vision.request(vision.PROMPT_V2, b"\xff\xd8\xff")
    assert body["response_format"]["json_schema"]["strict"] is True
    schema = body["response_format"]["json_schema"]["schema"]
    assert set(schema["properties"]["fields"]["required"]) == set(vision.FIELD_NAMES)
    assert body["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_a_live_call_needs_your_settings(monkeypatch):
    import pytest

    for k in ("VISION_BASE_URL", "VISION_API_KEY", "VISION_MODEL"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(SystemExit):
        vision.call_live("v2", documents.get("D036").path)
