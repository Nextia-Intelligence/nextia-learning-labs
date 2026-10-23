"""Kill switches and containment at the model gateway: a capability for everyone, a draining agent, the levels."""

from conftest import stream
from estate import kill, switches

TRIAGE = dict(stream("ticket-triage")[0]["body"], model="fast-small")
STRONG = dict(stream("support-workflow__chat-strong")[0]["body"], model="strong-reasoning")


def post(c, token, body=TRIAGE, **headers):
    return c.post("/v1/chat/completions", json=body, headers={"authorization": f"Bearer {token}", **headers})


def test_a_capability_kill_switch_stops_every_agent_that_uses_it(estate, gateway):
    from estate import kill

    kill.add("capability", "strong-reasoning", "usr-kwame", "a bad model change")
    r = post(gateway(), estate.token("support-workflow"), STRONG)
    assert r.status_code == 403 and r.json()["error"]["code"] == "stopped"
    assert post(gateway(), estate.token("ticket-triage")).status_code == 200


def test_a_draining_agent_finishes_its_run_but_starts_no_new_one(estate, gateway):
    c = gateway()
    t = estate.token("support-workflow")
    unit = [r for r in stream("support-workflow__chat-strong") if r["group"] == "T-80008" and r["repeat"] == 1]
    assert post(c, t, dict(unit[0]["body"], model="strong-reasoning"), **{"x-run-id": "run-1"}).status_code == 200
    estate.registry.set_status("support-workflow", "draining", "usr-kwame", "replace the prompt")
    c2 = gateway()
    if len(unit) > 1:
        assert post(c2, t, dict(unit[1]["body"], model="strong-reasoning"), **{"x-run-id": "run-1"}).status_code == 200
    r = post(c2, t, STRONG, **{"x-run-id": "run-2"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "agent_draining"


def test_a_switch_needs_a_reason_and_can_be_lifted(estate):
    import pytest

    with pytest.raises(ValueError):
        kill.add("writes", "*", "usr-kwame", "")
    sid = kill.add("writes", "*", "usr-kwame", "drill")
    assert switches.blocked(estate.snapshot(), "support-workflow", tool="orders.request_refund", write=True)
    kill.lift(sid, "usr-kwame", "drill over")
    assert switches.blocked(estate.snapshot(), "support-workflow", tool="orders.request_refund", write=True) is None


def test_everything_stops_every_call(estate, gateway):
    kill.add("everything", "*", "usr-kwame", "a serious incident")
    r = post(gateway(), estate.token("ticket-triage"))
    assert r.status_code == 403 and "every AI call is stopped" in r.json()["error"]["message"]
