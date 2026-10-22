"""Staged configuration changes: a canary replica first, then everyone, or back; and the canary's verdict."""

from conftest import stream
from estate import configstore

TRIAGE = dict(stream("ticket-triage")[0]["body"], model="fast-small")
BAD = {"id": "long-numbers", "kind": "pattern", "pattern": r"\d{6,}", "action": "block"}


def test_a_canary_version_reaches_only_the_canary_replicas_until_promote():
    v1 = configstore.publish("usr-kwame", "first")
    v2 = configstore.publish("usr-kwame", "a new guardrail", stage="canary")
    assert (configstore.version_for("a"), configstore.version_for("b")) == (v2, v1)
    assert configstore.promote("usr-kwame") == v2
    assert configstore.version_for("b") == v2


def test_rollback_during_a_canary_returns_everyone_to_the_stable_version():
    v1 = configstore.publish("usr-kwame", "first")
    configstore.publish("usr-kwame", "bad", stage="canary")
    assert configstore.rollback("usr-kwame", "the canary failed") == v1
    assert configstore.version_for("a") == v1


def test_the_watch_rolls_back_a_canary_that_fails(estate, gateway):
    content = configstore.gather()
    content["settings"]["guardrails"].append(BAD)
    content["settings"]["rollout"]["watch_requests"] = 5
    configstore.publish("usr-tomas", "block long numbers", stage="canary", content=content)
    a, b = gateway("a"), gateway("b")
    t = estate.token("ticket-triage")
    body = TRIAGE                                             # its ticket has an order number: LK-104233
    for _ in range(5):
        assert a.post("/v1/chat/completions", json=body, headers={"authorization": f"Bearer {t}"}).status_code == 400
        assert b.post("/v1/chat/completions", json=body, headers={"authorization": f"Bearer {t}"}).status_code == 200
    v = configstore.watch()
    assert v["seen"] == 5 and v["errors"] == 5 and v["state"].startswith("rolled back")


def test_the_watch_promotes_a_canary_that_works(estate, gateway):
    content = configstore.gather()
    content["settings"]["rollout"]["watch_requests"] = 3
    configstore.publish("usr-kwame", "a harmless change", stage="canary", content=content)
    a = gateway("a")
    t = estate.token("ticket-triage")
    for _ in range(3):
        a.post("/v1/chat/completions", json=TRIAGE, headers={"authorization": f"Bearer {t}"})
    assert configstore.watch()["state"].startswith("promoted")
