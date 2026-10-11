"""New tickets and their AI work during the request (the scaling course, Modules 1 and 2;
from Module 4 the default is the queue: these tests ask for INTAKE_MODE=async)."""

from fakes import fake_provider

TICKET = {
    "customer_id": "C-0022",
    "subject": "Charged twice for order LK-182074",
    "body": "My card was charged two times. Please refund one payment.",
}


def test_a_new_ticket_is_triaged_and_embedded(make_api, conn):
    api = make_api(intake_mode="async")
    r = api.post("/v1/tickets", json=TICKET)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["ticket_id"] == "T-500001"
    assert (body["team"], body["needs_human"], body["priority"]) == ("payment", False, 2)
    assert [run["task"] for run in body["ai_runs"]] == ["triage", "embed"]
    assert body["ai_runs"][0]["model"] == "gpt-6-luna-2026-09-22"  # the model version
    assert body["ai_runs"][1]["model"].endswith("(simulated)")
    timing = r.headers["Server-Timing"]
    for part in ("db;dur=", "triage;dur=", "embed;dur="):
        assert part in timing
    row = conn.execute(
        "SELECT team, priority, needs_human FROM tickets WHERE ticket_id = 'T-500001'"
    ).fetchone()
    assert row == {"team": "payment", "priority": 2, "needs_human": False}
    runs = conn.execute(
        "SELECT task, prompt_version, finish_reason FROM ai_runs WHERE ticket_id = 'T-500001'"
        " ORDER BY run_id"
    )
    assert [tuple(x.values()) for x in runs] == [
        ("triage", "assistant-v2", "stop"),
        ("embed", None, None),
    ]
    vec = conn.execute(
        "SELECT embedding_version FROM ticket_embeddings WHERE ticket_id = 'T-500001'"
    ).fetchone()
    assert vec == {"embedding_version": "embed-small-384-v1"}


def test_an_unknown_customer_is_404(make_api):
    r = make_api(intake_mode="async").post("/v1/tickets", json={**TICKET, "customer_id": "C-9999"})
    assert r.status_code == 404


def test_a_busy_provider_gives_503_and_the_ticket_is_lost(make_api, conn):
    r = make_api(intake_mode="async", provider=fake_provider(fail="quota")).post(
        "/v1/tickets", json=TICKET
    )
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "ai_busy"
    assert r.headers["Retry-After"] == "1"  # from retry-after-ms (600 ms), rounded up
    # Everything was one transaction: no AI result, so no ticket either.
    assert (
        conn.execute("SELECT count(*) AS n FROM tickets WHERE ticket_id LIKE 'T-5%'").fetchone()[
            "n"
        ]
        == 0
    )


def test_an_outage_gives_503_and_a_bad_answer_502(make_api):
    r = make_api(intake_mode="async", provider=fake_provider(fail="outage")).post(
        "/v1/tickets", json=TICKET
    )
    assert (r.status_code, r.json()["error"]["code"]) == (503, "ai_unavailable")
    r = make_api(intake_mode="async", provider=fake_provider(fail="bad")).post(
        "/v1/tickets", json=TICKET
    )
    assert (r.status_code, r.json()["error"]["code"]) == (502, "ai_bad_answer")
