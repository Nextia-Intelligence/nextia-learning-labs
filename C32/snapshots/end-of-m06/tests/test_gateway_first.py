"""The gateway's first checks (the registration module): identity, registration and capability."""

from conftest import stream

TRIAGE = dict(stream("ticket-triage")[0]["body"], model="fast-small")


def post(c, token, body=TRIAGE, **headers):
    h = {"authorization": f"Bearer {token}"} if token else {}
    return c.post("/v1/chat/completions", json=body, headers={**h, **headers})


def test_a_registered_agent_gets_an_answer_and_the_name_of_the_model(estate, gateway):
    r = post(gateway(), estate.token("ticket-triage"))
    assert r.status_code == 200
    assert r.headers["x-gateway-model"] == "chat-small (gpt-6-luna-2026-09-22)"
    assert r.headers["x-gateway-capability"] == "fast-small"


def test_no_token_no_call(gateway):
    r = post(gateway(), "")
    assert r.status_code == 401 and r.json()["error"]["code"] == "missing_token"


def test_a_token_for_the_tool_gateway_is_refused(estate, gateway):
    r = post(gateway(), estate.token("ticket-triage", "tool-gateway"))
    assert r.status_code == 401 and r.json()["error"]["code"] == "wrong_audience"


def test_a_provider_key_is_not_a_token(gateway):
    r = post(gateway(), "sim-az-service-team-0001")
    assert r.status_code == 401 and r.json()["error"]["check"] == "identity"


def test_an_agent_that_is_not_registered_is_refused(estate, gateway):
    snap = estate.snapshot()
    del snap["agents"]["ticket-triage"]                  # as if it were never registered
    r = post(gateway(snapshot=snap), estate.token("ticket-triage"))
    assert r.status_code == 403 and r.json()["error"]["code"] == "not_registered"


def test_a_suspended_agent_is_refused(estate, gateway):
    t = estate.token("ticket-triage")                    # a token issued before the suspension still works...
    estate.registry.set_status("ticket-triage", "suspended", "usr-kwame", "test")
    r = post(gateway(), t)                               # ...until the replica sees the suspension
    assert r.status_code == 403 and r.json()["error"]["code"] == "agent_suspended"


def test_an_agent_asks_only_for_its_capabilities(estate, gateway):
    r = post(gateway(), estate.token("ticket-triage"), dict(TRIAGE, model="strong-reasoning"))
    assert r.status_code == 403 and r.json()["error"]["code"] == "capability_not_allowed"
    r = post(gateway(), estate.token("ticket-triage"), dict(TRIAGE, model="gpt-6-luna"))
    assert r.status_code == 400 and r.json()["error"]["code"] == "unknown_capability"


def test_an_old_model_name_works_with_a_warning(estate, gateway):
    r = post(gateway(), estate.token("ticket-triage"), dict(TRIAGE, model="chat-small"))
    assert r.status_code == 200 and "old alias of the capability fast-small" in r.headers["x-gateway-warning"]


def test_revoked_credentials_kill_the_tokens_already_issued(estate, gateway):
    import time

    t = estate.token("ticket-triage")
    time.sleep(1.1)
    estate.identity.revoke("ticket-triage", "usr-kwame", "the secret leaked")
    r = post(gateway(), t)
    assert r.status_code == 401 and r.json()["error"]["code"] == "token_revoked"
