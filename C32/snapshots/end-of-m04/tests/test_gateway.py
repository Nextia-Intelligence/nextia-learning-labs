"""The model gateway's whole path: usage, limits, data classes, guardrails, routing and failure modes."""

import pytest

from conftest import stream
from estate.usage import UsageStore

TRIAGE = dict(stream("ticket-triage")[0]["body"], model="fast-small")
STRONG = dict(stream("support-workflow__chat-strong")[0]["body"], model="strong-reasoning")
CARD = "4539 1488 0343 6467"          # a made-up number that passes the Luhn check


def post(c, token, body=TRIAGE, **headers):
    return c.post("/v1/chat/completions", json=body, headers={"authorization": f"Bearer {token}", **headers})


def calls():
    return UsageStore().rows("select * from model_calls order by id")


def test_every_call_is_recorded_without_its_text(estate, gateway):
    r = post(gateway(), estate.token("ticket-triage"), traceparent="00-" + "a" * 32 + "-" + "b" * 16 + "-01")
    row = calls()[-1]
    assert (row["agent_id"], row["team"], row["capability"], row["deployment"], row["outcome"]) == \
        ("ticket-triage", "service", "fast-small", "chat-small", "ok")
    assert row["tokens_in"] == r.json()["usage"]["prompt_tokens"] and row["cost_usd"] > 0
    assert row["traceparent"].startswith("00-aaaa")
    assert "Broken" not in str(row) and "bird bath" not in str(row)        # no prompt or answer text


def test_a_capability_without_tools_refuses_tools(estate, gateway):
    body = dict(STRONG, tools=[{"type": "function", "function": {"name": "x", "parameters": {}}}])
    r = post(gateway(), estate.token("support-workflow"), body)
    assert r.status_code == 400 and r.json()["error"]["code"] == "feature_not_in_contract"


def test_payment_data_never_goes_to_a_model(estate, gateway):
    r = post(gateway(), estate.token("ticket-triage"), **{"x-data-class": "payment"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "data_class_not_allowed"
    r = post(gateway(), estate.token("doc-assistant"), dict(TRIAGE), **{"x-data-class": "personal"})
    assert r.status_code == 403                          # the document assistant is registered for internal data only


def test_the_run_step_limit_stops_a_loop(estate, gateway):
    c = gateway()
    t = estate.token("release-judge")                    # max_calls_per_run: 1
    body = dict(stream("release-judge__chat-strong")[0]["body"], model="strong-reasoning")
    codes = [post(c, t, body, **{"x-run-id": "loop-1"}).status_code for _ in range(3)]
    assert codes == [200, 429, 429]
    assert calls()[-1]["check_name"] == "step_limit"


def test_the_budget_is_a_hard_stop_with_a_warning_before(estate, gateway):
    snap = estate.snapshot()
    snap["agents"]["release-judge"]["budget_usd_month"] = 0.01
    c = gateway(snapshot=snap)
    t = estate.token("release-judge")
    body = dict(stream("release-judge__chat-strong")[0]["body"], model="strong-reasoning")
    seen = []
    for i in range(6):
        r = post(c, t, body, **{"x-run-id": f"r{i}"})
        seen.append((r.status_code, "x-gateway-budget-warning" in r.headers))
    assert (200, True) in seen and seen[-1] == (429, False)
    assert calls()[-1]["check_name"] == "budget"


def test_the_rate_limit_counts_every_replica(estate, gateway):
    snap = estate.snapshot()
    snap["agents"]["ticket-triage"]["limits"]["requests_per_minute"] = 2
    a, b = gateway("a", snapshot=snap), gateway("b", snapshot=snap)
    t = estate.token("ticket-triage")
    codes = [post(a, t).status_code, post(b, t).status_code, post(a, t).status_code]
    assert codes == [200, 200, 429]                       # the counters are shared, not one per replica


def test_a_card_number_is_redacted_before_it_leaves(estate, gateway):
    body = dict(TRIAGE)
    body["messages"] = [dict(m) for m in TRIAGE["messages"]]
    body["messages"][1]["content"] += f" My card is {CARD}."
    r = post(gateway(), estate.token("ticket-triage"), body)
    assert r.headers["x-gateway-redacted"] == "card-numbers: 1 card number(s) redacted"
    assert r.status_code == 422                            # the redacted request is a new request: no recording


def test_a_secret_in_a_prompt_is_blocked(estate, gateway):
    body = dict(TRIAGE)
    body["messages"] = [dict(m) for m in TRIAGE["messages"]]
    body["messages"][1]["content"] += " my key is sim-az-service-team-0001"
    r = post(gateway(), estate.token("ticket-triage"), body)
    assert r.status_code == 400 and r.json()["error"]["code"] == "blocked_by_guardrail"


def test_a_provider_outage_falls_back_to_the_second_region(estate, gateway, sim_client):
    sim_client.post("/admin/control", json={"provider": "azure", "mode": "down"})
    r = post(gateway(), estate.token("ticket-triage"))
    assert r.status_code == 200 and r.headers["x-gateway-provider"] == "azure-canada"
    assert "fallback" in r.headers["x-gateway-fallback"] and calls()[-1]["fallback"] == 1


def test_no_provider_left_is_a_clear_refusal(estate, gateway, sim_client):
    sim_client.post("/admin/control", json={"provider": "*", "mode": "down"})
    r = post(gateway(), estate.token("ticket-triage"))
    assert r.status_code == 503 and r.json()["error"]["code"] == "no_provider_available"


def test_a_request_error_is_not_retried_elsewhere(estate, gateway):
    r = post(gateway(), estate.token("ticket-triage"), dict(TRIAGE, max_completion_tokens=999))
    assert r.status_code == 422 and r.headers["x-gateway-upstream-status"] == "422"
    assert "x-gateway-fallback" not in r.headers


def test_a_pin_refuses_a_changed_model(estate, gateway):
    snap = estate.snapshot()
    snap["agents"]["release-judge"]["pins"] = {"strong-reasoning": {"deployment": "chat-strong",
                                                                    "model_version": "gpt-6.1-sol-2026-11-30",
                                                                    "retire_by": "2027-03-31"}}
    body = dict(stream("release-judge__chat-strong")[0]["body"], model="strong-reasoning")
    r = post(gateway(snapshot=snap), estate.token("release-judge"), body)
    assert r.status_code == 502 and r.json()["error"]["code"] == "pinned_model_changed"


@pytest.mark.parametrize("agent,status", [("doc-assistant", 200), ("support-workflow", 503)])
def test_an_old_configuration_fails_open_or_closed_by_risk_tier(estate, gateway, agent, status):
    from gateway.config import ConfigCache

    now = [0.0]
    cache = ConfigCache("a", clock=lambda: now[0])
    cache.set(estate.snapshot())
    now[0] = 1000.0                                        # far beyond max_stale_seconds
    body = {"doc-assistant": dict(stream("doc-assistant__chat")[0]["body"], model="fast-small"),
            "support-workflow": STRONG}[agent]
    r = post(gateway(cache=cache), estate.token(agent), body, **{"x-data-class": "internal"} if agent ==
             "doc-assistant" else {})
    assert r.status_code == status
    if status == 200:
        assert "fail open (low risk)" in r.headers["x-gateway-degraded"]
    else:
        assert r.json()["error"]["code"] == "control_unavailable"


def test_with_the_usage_store_down_low_risk_is_counted_on_the_replica(estate, gateway):
    c = gateway()
    c.post("/admin/faults", json={"usage_store": "down"})
    body = dict(stream("doc-assistant__chat")[0]["body"], model="fast-small")
    r = post(c, estate.token("doc-assistant"), body, **{"x-data-class": "internal"})
    assert r.status_code == 200 and "budgets cannot be checked across replicas" in r.headers["x-gateway-degraded"]
    assert post(c, estate.token("support-workflow"), STRONG).status_code == 503
    c.post("/admin/faults", json={"usage_store": "up"})
    post(c, estate.token("doc-assistant"), body, **{"x-data-class": "internal"})
    assert len([r for r in calls() if r["agent_id"] == "doc-assistant"]) == 2      # the kept row was written


def test_fail_open_budgets_count_from_the_last_total_each_replica_read(estate, gateway):
    """With the usage store down, each replica counts its own calls on top of the last total it read: with
    several replicas an agent can spend more than its budget. This test shows it on two replicas."""
    snap = estate.snapshot()
    snap["agents"]["doc-assistant"]["budget_usd_month"] = 0.0004
    a, b = gateway("a", snapshot=snap), gateway("b", snapshot=snap)
    body = dict(stream("doc-assistant__chat")[0]["body"], model="fast-small")
    t = estate.token("doc-assistant")
    h = {"authorization": f"Bearer {t}"}
    assert a.post("/v1/chat/completions", json=body, headers=h).status_code == 200      # a reads the total: 0
    assert b.post("/v1/chat/completions", json=body, headers=h).status_code == 200      # b reads one call
    for c in (a, b):
        c.post("/admin/faults", json={"usage_store": "down"})
    served = sum(c.post("/v1/chat/completions", json=body, headers=h).status_code == 200 for c in (a, b, a, b, a, b))
    one = calls()[0]["cost_usd"]
    assert served >= 2 and 2 * one + served * one > 0.0004 + one          # more than the budget, together

