import json

import pytest
from fastapi.testclient import TestClient

from larkroute import model_store, service, tfidf


@pytest.fixture
def client(small_train, tmp_path, monkeypatch):
    monkeypatch.setattr(model_store, "MODELS", tmp_path / "models")
    monkeypatch.setattr(service, "QUEUE", tmp_path / "queue")
    model = tfidf.logistic_regression().fit(small_train["text"], small_train["route"])
    model_store.save("test-1", model, {"routes": list(model.classes_), "label_version": "labels-test",
                                       "thresholds": {"decide": 0.6, "person_below": 0.2}})
    model_store.set_current("test-1")
    with TestClient(service.app) as c:
        yield c


def test_every_answer_has_the_model_and_label_versions(client):
    r = client.post("/route", json={"message_id": "M-999001", "text": "Where is my parcel? Order LK-123456.",
                                    "channel": "chat"})
    assert r.status_code == 200
    body = r.json()
    assert body["model_version"] == "test-1" and body["label_version"] == "labels-test"
    assert body["zone"] in ("decide", "review", "person") and 0 <= body["confidence"] <= 1
    assert client.get("/health").json()["model_version"] == "test-1"


@pytest.mark.parametrize("payload", [
    {"message_id": "M-1", "text": ""},
    {"message_id": "M-1", "text": "   "},
    {"message_id": "M-1", "text": "x" * 5001},
    {"message_id": "not an id", "text": "hello"},
    {"message_id": "M-1", "text": "hello", "channel": "fax"},
    {"text": "hello"},
])
def test_invalid_input_is_refused(client, payload):
    assert client.post("/route", json=payload).status_code == 422


def test_the_log_has_no_message_text(client):
    client.post("/route", json={"message_id": "M-999002", "text": "my secret words about a parcel"})
    log = (service.QUEUE / "decisions.jsonl").read_text()
    assert "secret" not in log and json.loads(log.splitlines()[-1])["message_id"] == "M-999002"


def test_a_version_is_never_overwritten(client):
    with pytest.raises(SystemExit):
        model_store.save("test-1", None, {})
