"""The simulated AI provider: shape of the answers, times from the recordings, the quota."""

import statistics

from fastapi.testclient import TestClient

from simulator import model, replay
from simulator.app import Settings, create_app
from simulator.quota import Quota
from ticket_api import ai, assistant


def make(monkeypatch, **env) -> TestClient:
    monkeypatch.setenv("SIM_SPEED", "0")  # no waiting in the tests
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return TestClient(create_app(Settings()))


def test_answers_have_the_openai_shape(monkeypatch):
    sim = make(monkeypatch)
    r = sim.post(
        "/v1/chat/completions", json=assistant.triage_request("Charged twice, refund please")
    )
    assert r.status_code == 200 and r.headers["X-Simulated"] == "true"
    assert assistant.parse_triage(r.json()).team == "payment"
    assert r.json()["model"] == "gpt-6-luna-2026-09-22"
    assert r.json()["simulator"]["evidence"] == "simulated"  # not a recorded request
    r = sim.post("/v1/embeddings", json=ai.embed_request("Charged twice", "refund please"))
    assert len(ai.parse_embedding(r.json())) == 384


def test_a_recorded_ticket_gets_a_real_recorded_answer():
    """Replay: the evaluation course's request for T-64740 (a parasol fell toward a child)."""
    import json
    import random

    ticket = next(
        json.loads(line)
        for line in open("data/practice/tickets.jsonl", encoding="utf-8")
        if '"T-64740"' in line
    )
    rows = replay.recordings()[replay.request_key(assistant.triage_request(ticket["message"]))]
    assert {r["case_id"] for r in rows} == {"T-64740"} and len(rows) == 5  # dev: 5 repeats
    body = assistant.triage_request(ticket["message"])
    answer, ms = model.triage_answer(body, "chat-small", random.Random(3), "gpt-6-luna-2026-09-22")
    assert answer["simulator"]["evidence"] == "replayed" and ms > 500
    assert assistant.parse_triage(answer).needs_human is True  # prompt v2 sends it to a person
    v3 = [
        r
        for r in replay.recordings()[
            replay.request_key(assistant.triage_request(ticket["message"], "assistant-v3"))
        ]
    ]
    assert any(r["finish_reason"] == "length" and r["content"] == "" for r in v3)


def test_times_come_from_the_recordings():
    import random

    rng = random.Random(1)
    times = [model.sample_latency_ms("draft_reply", rng) for _ in range(2000)]
    recorded = model.CALIBRATION["latency_ms"]["draft_reply"]
    assert min(recorded) <= min(times) and max(times) <= max(recorded)
    assert abs(statistics.median(times) - statistics.median(recorded)) < 60


def test_similar_texts_get_similar_vectors():
    a = model.embedding("my parcel was not delivered")
    b = model.embedding("the parcel was not delivered yet")
    c = model.embedding("reset my password please")
    dot = lambda x, y: sum(p * q for p, q in zip(x, y, strict=True))  # noqa: E731
    assert dot(a, b) > dot(a, c)


def test_the_quota_refuses_with_two_hints():
    now = [0.0]
    q = Quota(rpm=6, tpm=None, burst_seconds=60, clock=lambda: now[0])
    assert [q.try_take(1) for _ in range(6)] == [None] * 6
    wait = q.try_take(1)
    assert wait == 10.0  # one request comes back every 10 seconds
    now[0] = 10.0
    assert q.try_take(1) is None


def test_quota_mode_sends_429_with_retry_after(monkeypatch):
    sim = make(monkeypatch, SIM_MODE="quota")
    q = {"question": "x"}
    statuses = [
        sim.post(
            "/v1/chat/completions", json=ai.answer_request(**q, documents=[], tickets=[])
        ).status_code
        for _ in range(15)
    ]
    assert statuses.count(200) == 10 and statuses.count(429) == 5
    r = sim.post("/v1/chat/completions", json=ai.answer_request(**q, documents=[], tickets=[]))
    assert r.headers["Retry-After"] == "30" and int(r.headers["retry-after-ms"]) > 0


def test_outage_mode_and_stats(monkeypatch):
    sim = make(monkeypatch)
    sim.post("/admin/mode", json={"mode": "outage"})
    assert sim.post("/v1/embeddings", json=ai.embed_request("a", "b")).status_code == 503
    assert sim.get("/admin/stats").json()["calls"] == {"embed": {"503": 1}}
    sim.post("/admin/reset")
    assert sim.get("/admin/stats").json()["mode"] == "normal"
