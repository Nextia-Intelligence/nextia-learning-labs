"""The remap gate on the real recordings: Omar's cheaper model behind strong-reasoning."""

from conftest import PROJECT
from estate import remap

WHAT_IF = str(PROJECT / "registrations" / "what-if" / "ticket-triage-on-strong.yaml")


def test_the_cheaper_model_fails_both_real_consumers():
    r = remap.gate("strong-reasoning", "azure", "chat-small", {"reasoning_effort": "none"})
    by = {c["consumer"]: c for c in r["consumers"]}
    assert set(by) == {"release-judge", "support-workflow"}
    wf, judge = by["support-workflow"], by["release-judge"]
    assert (wf["current"]["passed"], wf["candidate"]["passed"], wf["candidate"]["total"]) == (70, 64, 70)
    assert wf["candidate"]["unexpected_changes"] == 2 and wf["verdict"] == "fail"
    assert (judge["current"]["passed"], judge["candidate"]["passed"], judge["candidate"]["total"]) == (99, 70, 101)
    assert r["decision"] == "block"
    assert wf["candidate"]["cost_usd"] < wf["current"]["cost_usd"] / 10      # the reason Omar asked


def test_an_average_can_pass_while_one_consumer_fails():
    """Constructed: a what-if consumer (the triage service on strong-reasoning) whose answers are real recordings."""
    r = remap.gate("strong-reasoning", "azure", "chat-small", {"reasoning_effort": "none"},
                   consumers_only=["support-workflow", "ticket-triage-on-strong"], also=[WHAT_IF])
    by = {c["consumer"]: c for c in r["consumers"]}
    assert by["ticket-triage-on-strong"]["candidate"]["passed"] == 90        # the evaluation course's 90 of 102
    assert by["ticket-triage-on-strong"]["current"]["passed"] == 87          # chat-strong: 87 of 102
    assert r["average_candidate"] >= 0.85 and by["support-workflow"]["verdict"] == "fail"
    assert r["decision"] == "block"


def test_a_consumer_without_an_evaluation_blocks_a_remap():
    r = remap.gate("fast-small", "azure", "chat-strong", consumers_only=["doc-assistant"])
    assert r["consumers"][0]["verdict"] == "no evidence" and r["decision"] == "block"


def test_the_report_names_every_consumer():
    text = remap.render(remap.gate("strong-reasoning", "azure", "chat-small", {"reasoning_effort": "none"},
                                   consumers_only=["release-judge"]))
    assert "release-judge      FAIL  agreement 70/101 = 0.693 (minimum 0.9)" in text
    assert "Decision: BLOCK" in text
