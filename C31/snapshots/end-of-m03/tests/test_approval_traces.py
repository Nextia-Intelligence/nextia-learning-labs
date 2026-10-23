"""An approval splits a run into two traces joined by a span link; who approved and how long it waited."""

from obs.model import Telemetry
from resolver import conventions as c
from resolver.__main__ import main


def started(capsys, *args) -> str:
    """A fresh practice database, then run a ticket; the run ID from the first line ("Run <id> | ...")."""
    main(["reset"])
    capsys.readouterr()
    main(["run", *args])
    return capsys.readouterr().out.split()[1]


def test_two_linked_traces_and_the_double_refund(telemetry_files, capsys):
    rid = started(capsys, "T-90104", "--variant", "agent_structured", "--model", "chat-strong")
    main(["approve", rid, "--as", "agent", "--name", "Sam",
          "--fault", "request_refund:timeout_after_write", "--naive-retry"])
    out = capsys.readouterr().out
    assert "Reply sent. Ticket: resolved." in out
    telemetry_files.flush()
    run = next(iter(Telemetry(telemetry_files.folder).runs.values()))
    assert len(run.trace_ids) == 2
    request = next(s for s in run.spans if s.name == "approval.request")
    decision = run.decision
    assert decision.links and decision.links[0][:2] == (request.trace_id, request.span_id)
    assert decision.get(c.APPROVER) == "usr-sam" and decision.get(c.APPROVER_ROLE) == "agent"
    assert decision.get(c.APPROVAL_WAIT) is not None and decision.start >= request.end
    refunds = [s for s in run.writes if s.tool == "request_refund"]
    assert [s.get(c.WRITE_OUTCOME) for s in refunds] == ["timeout", "done"]
    assert refunds[0].get(c.IDEMPOTENCY_KEY) != refunds[1].get(c.IDEMPOTENCY_KEY)
    assert refunds[0].get(c.OPERATION_ID) == refunds[1].get(c.OPERATION_ID)


def test_the_safe_retry_reconciles_and_writes_once(telemetry_files, capsys):
    rid = started(capsys, "T-90104", "--variant", "agent_structured", "--model", "chat-strong")
    main(["approve", rid, "--as", "agent", "--fault", "request_refund:timeout_after_write"])
    telemetry_files.flush()
    run = next(iter(Telemetry(telemetry_files.folder).runs.values()))
    assert [s.get(c.WRITE_OUTCOME) for s in run.writes] == ["timeout"]
    rec = [s for s in run.spans if s.name.startswith("reconcile")]
    assert rec and rec[0].get("larkfield.reconcile.found") is True


