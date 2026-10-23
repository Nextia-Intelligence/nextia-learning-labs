"""The audit trail: fixed schema, append-only chain, anchor, pseudonyms, never sampled."""

import json

import pytest
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF

from auditstore.schema import AuditEventError
from auditstore.store import AuditStore, record_hash
from resolver import telemetry
from resolver.__main__ import main


def event(n=1, **kw):
    e = {"schema": "larkfield.audit/1", "event_id": f"e{n}", "type": "write", "at": "2026-10-15T12:47:12+00:00",
         "actor": {"kind": "system", "id": "support-workflow"}, "run_id": "R-1", "ticket_id": "T-1", "trace_id": "",
         "span_id": "", "subject": {"customer_id": "C-1", "order_id": "LK-000001"}, "action": {"tool": "request_refund"},
         "authority": {}, "evidence": []}
    e.update(kw)
    return e


def test_the_chain_verifies_and_finds_a_changed_record(tmp_path):
    s = AuditStore(tmp_path / "audit.jsonl")
    for i in range(1, 6):
        s.append(event(i))
    assert s.verify()["ok"]
    lines = s.path.read_text().splitlines()
    rec = json.loads(lines[2])
    rec["event"]["action"]["tool"] = "reship_item"     # someone edits record 3 by hand
    lines[2] = json.dumps(rec)
    s.path.write_text("\n".join(lines) + "\n")
    v = s.verify()
    assert not v["ok"] and v["problems"][0].startswith("record 3: its content does not match its hash")
    recs = [json.loads(line) for line in lines]          # now compute record 3's hash and every later one again
    for i in range(2, 5):
        recs[i]["prev"] = recs[i - 1]["hash"]
        recs[i]["hash"] = record_hash(recs[i]["seq"], recs[i]["prev"], recs[i]["event"])
    s.path.write_text("".join(json.dumps(r) + "\n" for r in recs))
    v = s.verify()
    assert not v["ok"] and "as the anchor says, but its last hash is not the anchor's head" in v["problems"][0]


def test_removing_the_last_record_is_found_by_the_anchor(tmp_path):
    s = AuditStore(tmp_path / "audit.jsonl")
    for i in range(1, 4):
        s.append(event(i))
    s.path.write_text("\n".join(s.path.read_text().splitlines()[:2]) + "\n")
    v = s.verify()
    assert not v["ok"] and "the anchor says 3" in v["problems"][0]


def test_text_is_refused(tmp_path):
    with pytest.raises(AuditEventError, match="text fields"):
        AuditStore(tmp_path / "a.jsonl").append(event(action={"tool": "request_refund", "reply": "Hello"}))
    with pytest.raises(AuditEventError, match="looks like text"):
        AuditStore(tmp_path / "a.jsonl").append(event(action={"code": "x" * 81}))


def test_a_deletion_request_keeps_the_chain(tmp_path):
    s = AuditStore(tmp_path / "audit.jsonl")
    s.append(event(1))
    p = s.events()[0]["subject"]["customer"]
    assert p.startswith("cust:") and "C-1" not in s.path.read_text()
    assert s.find_pseudonym("C-1") == p and s.forget("C-1")
    assert s.find_pseudonym("C-1") is None and s.verify()["ok"]


def test_audit_events_are_never_sampled(tmp_path, capsys):
    t = telemetry.Telemetry(export="file", folder=tmp_path / "t", audit_path=tmp_path / "audit.jsonl", sampler=ALWAYS_OFF)
    old = telemetry.use(t)
    try:
        main(["run", "T-90103", "--variant", "agent", "--model", "chat-small"])
        t.flush()
        assert not (tmp_path / "t" / "traces.jsonl").exists()       # every trace sampled out
        types = [e["type"] for e in t.audit.events()]
        assert types.count("data_access") >= 1 and "proposal" in types
    finally:
        t.shutdown()
        telemetry.use(old)
