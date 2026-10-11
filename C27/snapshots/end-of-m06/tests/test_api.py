"""The backend's contract: validated endpoints, one error shape, uploads as jobs with states."""

from pathlib import Path

from tests.conftest import index_all, upload

DATA = Path(__file__).resolve().parent.parent / "data"
GIFT = DATA / "bramble" / "documents" / "gift-cards.md"


def test_health_and_ready(client):
    assert client.get("/health").json()["status"] == "ok"
    r = client.get("/ready")
    assert r.status_code == 200 and r.json()["status"] == "ready"


def test_an_upload_is_a_job_with_visible_states(client, token):
    r = upload(client, token("usr-ines"), "bramble", GIFT)
    assert r.status_code == 202 and r.json()["duplicate"] is False
    doc = r.json()["document"]
    assert doc["status"] == "uploaded" and doc["doc_key"] == "gift-cards" and doc["access"] == "public"
    assert r.headers["location"] == f"/v1/tenants/bramble/documents/{doc['document_id']}"
    assert index_all(client) == {"indexed": 1}
    after = client.get(r.headers["location"], headers=token("usr-ines")).json()["document"]
    assert after["status"] == "indexed" and after["chunk_count"] == 4 and after["error"] is None


def test_form_fields_win_over_the_files_metadata(client, token):
    r = upload(client, token("usr-ines"), "bramble", GIFT, access="staff", version="7")
    assert r.json()["document"]["access"] == "staff" and r.json()["document"]["version"] == "7"


def test_errors_have_one_shape(client, token):
    r = client.post("/v1/tenants/bramble/answers", json={"question": "?"}, headers=token("usr-ines"))
    body = r.json()
    assert r.status_code == 422 and body["code"] == "validation_error" and body["details"][0]["field"] == "question"
    assert set(body) == {"code", "message", "request_id", "details"} and r.headers["x-request-id"] == body["request_id"]
    r = client.get("/v1/tenants/bramble/documents/not-a-uuid", headers=token("usr-ines"))
    assert r.status_code == 404 and r.json()["code"] == "not_found"
    r = client.post("/v1/tenants/bramble/answers", json={"question": "ok?", "extra": 1}, headers=token("usr-ines"))
    assert r.status_code == 422


def test_a_question_returns_an_answer_with_citations(loaded, token):
    r = loaded.post("/v1/tenants/bramble/answers", json={"question": "How long is a gift card valid?"},
                    headers=token("usr-ines"))
    a = r.json()["answer"]
    assert r.status_code == 200 and a["answerable"] and a["provider"] == "mock"
    assert a["claims"][0]["citations"][0]["doc_key"] == "gift-cards"
    stored = loaded.get(r.json()["links"]["self"], headers=token("usr-ines")).json()["answer"]
    assert stored["question"] == "How long is a gift card valid?" and stored["answer"] == a["answer"]


def test_responses_are_not_cached_by_the_browser(client, token):
    r = client.get("/v1/tenants/bramble/documents", headers=token("usr-ines"))
    assert r.headers["cache-control"] == "no-store"
