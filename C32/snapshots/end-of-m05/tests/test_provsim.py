"""The provider simulator: real recorded answers byte for byte, the recorded feature errors, never an invented answer."""

import gzip
import json

from conftest import PROJECT, stream
from provsim import features
from provsim.store import Store, request_key

KEY = {"api-key": "sim-az-service-team-0001"}


def test_a_recorded_request_gets_its_recorded_answer(sim_client):
    row = stream("ticket-triage")[0]
    r = sim_client.post("/azure/v1/chat/completions", json=row["body"], headers={**KEY, "x-sim-repeat": "1"})
    assert r.status_code == 200
    assert r.json()["model"] == "gpt-6-luna-2026-09-22"
    assert r.headers["x-sim-source"] == "evaluation course: system_baseline.jsonl"
    assert r.headers["x-sim-match"] == "exact"
    answers = Store().answers(row["body"])
    assert r.json() == next(a.response for a in answers if a.repeat == 1)


def test_one_changed_character_is_another_request(sim_client):
    body = dict(stream("ticket-triage")[0]["body"])
    body["max_completion_tokens"] = 999
    r = sim_client.post("/azure/v1/chat/completions", json=body, headers=KEY)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "no_recording"
    assert "never invents" in r.json()["error"]["message"]


def test_embeddings_are_real_vectors(sim_client):
    row = next(r for r in stream("ticket-triage") if r["endpoint"] == "/v1/embeddings")
    r = sim_client.post("/azure/v1/embeddings", json=row["body"], headers=KEY)
    assert r.status_code == 200
    assert r.json()["model"] == "text-embedding-3-small"
    assert len(r.json()["data"][0]["embedding"]) == 384


def test_the_recorded_feature_errors(sim_client):
    small = stream("support-workflow__chat-small")[0]["body"]
    tools = [{"type": "function", "function": {"name": "x", "parameters": {"type": "object", "properties": {}}}}]
    cases = [
        ("chat-strong", {}, "chat-strong-no-tools", features.STRONG_TOOLS),
        ("chat-strong", {"reasoning_effort": "none"}, "chat-strong-no-none", features.STRONG_NONE),
        ("chat-small", {}, "chat-small-tools-need-none", features.SMALL_TOOLS),
    ]
    for deployment, extra, rule, error in cases:
        body = {k: v for k, v in small.items() if k != "reasoning_effort"}
        body.update(model=deployment, tools=tools, **extra)
        r = sim_client.post("/azure/v1/chat/completions", json=body, headers=KEY)
        assert (r.status_code, r.headers["x-sim-rule"], r.json()) == (400, rule, error)
    body = {k: v for k, v in small.items() if k != "reasoning_effort"}
    body.update(model="gemma3:4b", tools=tools)
    r = sim_client.post("/local/v1/chat/completions", json=body)
    assert r.status_code == 400 and r.json() == features.GEMMA_TOOLS


def test_the_rule_texts_are_the_recorded_ones():
    with gzip.open(PROJECT / "provsim" / "recordings" / "answers.jsonl.gz", "rt") as f:
        recorded = [json.loads(line)["error"]["body"] for line in f if '"error"' in line and json.loads(line).get("error")]
    for _, _, _, _, body, _ in features.RULES:
        assert body in recorded


def test_a_key_works_only_at_its_provider(sim_client):
    body = stream("ticket-triage")[0]["body"]
    assert sim_client.post("/azure/v1/chat/completions", json=body, headers={"api-key": "nope"}).status_code == 401
    r = sim_client.post("/fernway/v1/chat/completions", json=body, headers=KEY)
    assert r.status_code == 401


def test_the_egress_rule_lets_only_the_gateway_out(sim_client):
    body = stream("ticket-triage")[0]["body"]
    sim_client.post("/admin/settings", json={"egress": "gateway-only"})
    r = sim_client.post("/azure/v1/chat/completions", json=body, headers={**KEY, "x-sim-host": "triage-svc-01"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "egress_blocked"
    r = sim_client.post("/azure/v1/chat/completions", json=body, headers={"api-key": "sim-az-gateway-0009"})
    assert r.status_code == 200
    log = sim_client.get("/admin/egress").text.splitlines()
    assert log[0].startswith("time,source_host")
    assert ",triage-svc-01,larkfield-ai.openai.azure.example,azure,az-key-1,403," in log[1]


def test_the_bill_shows_key_ids_not_apps(sim_client):
    body = stream("ticket-triage")[0]["body"]
    for _ in range(3):
        sim_client.post("/azure/v1/chat/completions", json=body, headers=KEY)
    bill = sim_client.get("/admin/bill").text.splitlines()
    assert bill[0] == "month,provider,key_id,deployment,requests,tokens_in,tokens_out,cost_usd"
    assert ",azure,az-key-1,chat-small,3," in bill[1]


def test_practice_outages_are_labelled_simulated(sim_client):
    body = stream("ticket-triage")[0]["body"]
    sim_client.post("/admin/control", json={"provider": "azure", "mode": "down", "requests": 2})
    codes = [sim_client.post("/azure/v1/chat/completions", json=body, headers=KEY).status_code for _ in range(3)]
    assert codes == [503, 503, 200]
    sim_client.post("/admin/control", json={"provider": "azure", "mode": "rate_limit"})
    r = sim_client.post("/azure/v1/chat/completions", json=body, headers=KEY)
    assert r.status_code == 429 and r.headers["retry-after"] == "30" and r.headers["retry-after-ms"] == "1256"
    assert "simulated" in r.json()["error"]["message"]


def test_several_recorded_answers_are_given_in_turn():
    store = Store()
    body = next(r["body"] for r in stream("ticket-triage") if r["repeat"] == 2)
    picks = [store.pick(body).repeat for _ in range(6)]
    assert sorted(set(picks)) == [1, 2, 3, 4, 5]
    assert store.pick(body, repeat=3).repeat == 3


def test_the_key_ignores_reasoning_effort_only():
    body = stream("support-workflow__chat-small")[0]["body"]
    assert body["reasoning_effort"] == "none"         # the agents course sent it with every chat-small call
    assert request_key(body) == request_key({k: v for k, v in body.items() if k != "reasoning_effort"})
    assert request_key(body) != request_key(dict(body, model="chat-strong"))
