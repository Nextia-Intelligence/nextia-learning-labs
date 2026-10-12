"""Failure handling: refused files, duplicates, a slow or failing provider, and abstention."""

import time
from pathlib import Path

import pytest

from doc_assistant.providers import LiveProvider
from scripts.fake_provider import FakeProvider
from tests.conftest import upload

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.mark.parametrize("name, data, status, code", [
    ("notes.docx", b"PK\x03\x04 a word file", 415, "unsupported_file"),
    ("empty.md", b"", 422, "empty_file"),
    ("big.md", b"# Big\n\n" + b"x" * 5_000_001, 413, "file_too_large"),
])
def test_files_refused_at_once(client, token, tmp_path, name, data, status, code):
    f = tmp_path / name
    f.write_bytes(data)
    r = upload(client, token("usr-ines"), "bramble", f)
    assert r.status_code == status and r.json()["code"] == code


def test_bad_metadata_is_a_validation_error(client, token):
    r = upload(client, token("usr-ines"), "bramble", DATA / "bramble" / "documents" / "faq.md", access="everyone",
               effective_from="next week")
    assert r.status_code == 422 and {d["field"] for d in r.json()["details"]} == {"access", "effective_from"}


def test_the_same_file_twice_is_one_document(client, token):
    f = DATA / "bramble" / "documents" / "faq.md"
    first = upload(client, token("usr-ines"), "bramble", f)
    second = upload(client, token("usr-ines"), "bramble", f)
    assert first.status_code == 202 and second.status_code == 200 and second.json()["duplicate"] is True
    assert second.json()["document"]["document_id"] == first.json()["document"]["document_id"]
    other_shop = upload(client, token("usr-sam"), "larkfield", f)
    assert other_shop.status_code == 202   # another shop gets its own copy


def test_a_new_version_with_the_same_number_is_a_conflict(client, token, tmp_path):
    f = tmp_path / "faq.md"
    f.write_text((DATA / "bramble" / "documents" / "faq.md").read_text() + "\n## New\n\nA change.\n")
    upload(client, token("usr-ines"), "bramble", DATA / "bramble" / "documents" / "faq.md")
    r = upload(client, token("usr-ines"), "bramble", f)
    assert r.status_code == 409 and "version 4 of faq already exists" in r.json()["message"].lower()


def test_a_slow_provider_times_out_after_bounded_retries(loaded, token):
    with FakeProvider("slow", delay=5) as fake:
        loaded.app.state.provider = LiveProvider(fake.url, "", timeout_s=0.5, retries=2, sleep=lambda s: None)
        start = time.monotonic()
        r = loaded.post("/v1/tenants/bramble/answers", json={"question": "How long is a gift card valid?"},
                        headers=token("usr-ines"))
        took = time.monotonic() - start
    assert r.status_code == 504 and r.json()["code"] == "provider_timeout"
    assert len(fake.calls) == 3 and took < 3   # 1 try + 2 retries of 0.5 s each, not 5 s each


def test_a_failing_provider_is_503_with_retry_after(loaded, token):
    with FakeProvider("error") as fake:
        loaded.app.state.provider = LiveProvider(fake.url, "", timeout_s=2, retries=1, sleep=lambda s: None)
        r = loaded.post("/v1/tenants/bramble/answers", json={"question": "How long is a gift card valid?"},
                        headers=token("usr-ines"))
    assert r.status_code == 503 and r.json()["code"] == "provider_unavailable" and r.headers["retry-after"] == "30"
    assert len(fake.calls) == 2


def test_a_question_without_sources_is_answered_honestly(client, token):
    r = client.post("/v1/tenants/bramble/answers", json={"question": "How long is a gift card valid?"},
                    headers=token("usr-ines"))
    a = r.json()["answer"]
    assert r.status_code == 200 and not a["answerable"] and a["provider"] == "none"
    assert a["answer"] == "The documents do not answer this question."
