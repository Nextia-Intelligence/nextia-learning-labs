"""Adoption and friction: how far the gateway has spread, and what it refused."""

from datetime import datetime, timezone

from conftest import stream
from estate import adoption, clock


def test_adoption_counts_calls_through_and_around_the_gateway(tmp_path, estate, gateway):
    bill = tmp_path / "bill.csv"
    bill.write_text("month,provider,key_id,deployment,requests,tokens_in,tokens_out,cost_usd\n"
                    "2026-09,azure,az-key-9,chat-small,900,1,1,1.0\n2026-09,azure,az-key-1,chat-small,100,1,1,0.1\n")
    clock.set_replay_time(datetime(2026, 9, 15, 10, 0, tzinfo=timezone.utc))     # a replayed day in September
    c = gateway()
    body = dict(stream("ticket-triage")[0]["body"], model="fast-small")
    t = estate.token("ticket-triage")
    for model in ("fast-small", "fast-small", "strong-reasoning"):
        c.post("/v1/chat/completions", json=dict(body, model=model), headers={"authorization": f"Bearer {t}"})
    text = adoption.adoption(month="2026-09", bills=[bill])
    assert "Provider calls through the gateway: 900 of 1,000 (90.0%); around it: 100." in text
    assert "ticket-triage" in text and "1 of      3 refused (33.3%): capability 1" in text
