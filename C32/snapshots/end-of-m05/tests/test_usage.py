"""The usage store's reports: usage and cost per agent, team, capability and model."""

from conftest import stream
from estate import usage

TRIAGE = dict(stream("ticket-triage")[0]["body"], model="fast-small")


def some_traffic(estate, gateway, n=3):
    c = gateway()
    for _ in range(n):
        c.post("/v1/chat/completions", json=TRIAGE, headers={"authorization": f"Bearer {estate.token('ticket-triage')}"})
    c.post("/v1/chat/completions", json=dict(TRIAGE, model="strong-reasoning"),
           headers={"authorization": f"Bearer {estate.token('ticket-triage')}"})


def test_usage_by_agent_and_by_model(estate, gateway):
    some_traffic(estate, gateway)
    text = usage.usage_table("agent")
    assert text.splitlines()[2].startswith("ticket-triage") and " 4       3        1 " in text.splitlines()[2]
    assert "chat-small (gpt-6-luna-2026-09-22)" in usage.usage_table("model")


def test_the_store_counts_per_agent_and_team_per_window(estate, gateway):
    some_traffic(estate, gateway, 2)
    from estate import clock
    from estate.usage import UsageStore, windows

    w = windows(clock.iso())
    s = UsageStore()
    assert s.counter("ticket-triage", w["month"])["calls"] == 3       # the refused call counts as a request
    assert s.counter("team:service", w["day"])["cost_usd"] > 0
