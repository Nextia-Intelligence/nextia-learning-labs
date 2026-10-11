"""Telemetry with OpenTelemetry (the MLOps course, Module 3): one trace per ticket, events with
the request ID, GenAI attributes, redaction, sampling."""

import json
import random
from dataclasses import replace

import pytest
from conftest import TEST_SETTINGS
from test_jobs import TICKET, run_worker

from ops.__main__ import main
from ticket_api import telemetry


@pytest.fixture(scope="module")
def telemetry_file(tmp_path_factory):
    """Telemetry for this process, into one file (it starts once per process)."""
    path = tmp_path_factory.mktemp("telemetry") / "all.jsonl"
    started = telemetry.start(replace(TEST_SETTINGS, telemetry_file=str(path)), "ticket-tests")
    if not started:
        pytest.skip("telemetry was started before with other settings")
    return path


def records(path):
    telemetry.flush()
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_redaction_removes_text_and_masks_addresses():
    attrs = {
        "ticket.body": "My email is ana@example.com",
        "gen_ai.input.messages": "[...]",
        "note": "write to ana@example.com or call; card 4111 1111 1111 1111",
        "gen_ai.usage.input_tokens": 1902,
        "gen_ai.response.model": "gpt-6-luna-2026-09-22",
    }
    out = telemetry.redact(attrs)
    assert "ticket.body" not in out and "gen_ai.input.messages" not in out
    assert out["note"] == "write to [email] or call; card [card]"
    assert out["gen_ai.usage.input_tokens"] == 1902
    assert out["gen_ai.response.model"] == "gpt-6-luna-2026-09-22"  # a date is not a card


def test_inputs_are_described_without_their_text():
    assert telemetry.language_guess("Bonjour, je n'ai pas reçu mon colis pour la commande.") == "fr"
    assert telemetry.language_guess("My parcel did not arrive.") == "en"
    fp = telemetry.fingerprint("My parcel did not arrive.")
    assert len(fp) == 16 and fp == telemetry.fingerprint("My parcel did not arrive.")
    assert telemetry.customer_ref("C-0022") != "C-0022"


def test_sampling_keeps_about_the_share_asked_for():
    from opentelemetry.sdk.trace.sampling import Decision, TraceIdRatioBased

    sampler, rng = TraceIdRatioBased(0.1), random.Random(7)
    kept = sum(
        sampler.should_sample(None, rng.getrandbits(128), "t").decision
        == Decision.RECORD_AND_SAMPLE
        for _ in range(10_000)
    )
    assert 900 < kept < 1100


def test_one_trace_per_ticket_from_the_api_to_the_worker(
    telemetry_file, make_api, db_url, tmp_path
):
    api = make_api()
    r = api.post("/v1/tickets", json=TICKET)
    ticket = r.json()["ticket_id"]
    run_worker(db_url)
    rows = records(telemetry_file)
    received = next(
        x
        for x in reversed(rows)
        if x.get("event") == "ticket.received" and x["attributes"].get("ticket.id") == ticket
    )
    triaged = next(
        x
        for x in reversed(rows)
        if x.get("event") == "ticket.triaged" and x["attributes"].get("ticket.id") == ticket
    )
    assert received["attributes"]["http.status_code"] == 202
    assert received["trace_id"] == triaged["trace_id"]  # one trace
    assert received["attributes"]["request.id"] == triaged["attributes"]["request.id"]
    assert r.headers["X-Request-ID"] == received["attributes"]["request.id"]
    a = triaged["attributes"]
    assert a["outcome"] == "ok" and a["team"] == "payment" and a["prompt.version"] == "assistant-v2"
    assert a["gen_ai.usage.input_tokens"] > 1000 and a["cost_usd"] > 0
    spans = [x for x in rows if x["signal"] == "span" and x["trace_id"] == triaged["trace_id"]]
    names = {x["name"] for x in spans}
    assert {"POST /v1/tickets", "process ticket job", "triage", "chat chat-small"} <= names
    chat = next(x for x in spans if x["name"] == "chat chat-small")
    assert chat["attributes"]["gen_ai.operation.name"] == "chat"
    assert chat["attributes"]["gen_ai.response.finish_reasons"] == ["stop"]
    # no text of the ticket anywhere
    blob = json.dumps(rows)
    assert TICKET["body"] not in blob and "ticket.body" not in blob
    path = tmp_path / "copy.jsonl"
    path.write_text("".join(json.dumps(x) + "\n" for x in rows))
    assert main(["waterfall", str(path), "--ticket", ticket]) == 0


def test_a_ticket_without_an_answer_is_an_error_in_its_trace(telemetry_file, make_api, db_url):
    from fakes import fake_provider

    ticket = make_api().post("/v1/tickets", json=TICKET).json()["ticket_id"]
    run_worker(db_url, provider=fake_provider(fail="no_answer"), triage_fallback="none")
    rows = records(telemetry_file)
    triaged = next(
        x
        for x in reversed(rows)
        if x.get("event") == "ticket.triaged" and x["attributes"].get("ticket.id") == ticket
    )
    assert triaged["attributes"]["outcome"] == "no_answer"
    assert triaged["attributes"]["gen_ai.response.finish_reasons"] == "length"
    assert triaged["severity"] == "ERROR"
    job = next(
        x
        for x in rows
        if x["signal"] == "span"
        and x["name"] == "process ticket job"
        and x["trace_id"] == triaged["trace_id"]
    )
    assert job["status"] == "error" and job["attributes"]["app.outcome"] == "no_answer"


def test_privacy_scan_counts_without_printing(tmp_path, capsys):
    path = tmp_path / "t.jsonl"
    path.write_text(
        json.dumps(
            {
                "signal": "log",
                "time": 1,
                "event": "ticket.received",
                "attributes": {"ticket.id": "T-1", "ticket.body": "mail me: a@b.example"},
            }
        )
        + "\n"
    )
    assert main(["privacy", str(path)]) == 1
    out = capsys.readouterr().out
    assert "attribute ticket.body: 1" in out and "e-mail address: 1" in out
    assert "a@b.example" not in out


def test_prune_keeps_the_last_days(tmp_path, capsys):
    path = tmp_path / "t.jsonl"
    path.write_text(
        "".join(json.dumps({"signal": "log", "time": t}) + "\n" for t in (0, 86400 * 9))
    )
    assert main(["prune", str(path), "--days", "5", "--now", str(86400 * 10)]) == 0
    assert len(path.read_text().splitlines()) == 1
