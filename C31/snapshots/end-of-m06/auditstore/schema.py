"""The audit event: who did what, when, on whose authority and with what evidence. Fixed fields, no text.

Every event has the same top-level fields. `check()` refuses an event with a missing field, an unknown
type or a field that could carry text (a ticket, a prompt, an answer, a note). IDs, amounts, codes and
names of tools and rules are allowed; sentences are not.

    {"schema": "larkfield.audit/1", "event_id": "...", "type": "approval", "at": "2026-10-14T08:47:12+00:00",
     "actor": {"kind": "person", "id": "usr-sam", "role": "agent"},
     "run_id": "...", "ticket_id": "T-90104", "trace_id": "...", "span_id": "...",
     "subject": {"customer": "cust:3f9a...", "order_id": "LK-793996"},
     "action": {...}, "authority": {...}, "evidence": [...]}
"""

SCHEMA = "larkfield.audit/1"
TYPES = ("proposal", "approval", "refusal", "write", "data_access", "handoff", "run_closed")
ACTOR_KINDS = ("agent", "person", "system")
TOP = ("schema", "event_id", "type", "at", "actor", "run_id", "ticket_id", "trace_id", "span_id", "subject",
       "action", "authority", "evidence")
TEXT_FIELDS = ("text", "reply", "reason", "message", "prompt", "answer", "note", "body", "content", "goal")
MAX_STRING = 80   # longer strings are refused: they are probably text, not an ID or a code


class AuditEventError(ValueError):
    pass


def _walk(value, path):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in TEXT_FIELDS:
                raise AuditEventError(f"{path}.{k}: text fields are not allowed in an audit event")
            _walk(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _walk(v, f"{path}[{i}]")
    elif isinstance(value, str) and len(value) > MAX_STRING:
        raise AuditEventError(f"{path}: a string of {len(value)} characters looks like text, not an ID")


def check(event: dict) -> dict:
    missing = [k for k in TOP if k not in event]
    if missing:
        raise AuditEventError(f"missing fields: {', '.join(missing)}")
    extra = [k for k in event if k not in TOP]
    if extra:
        raise AuditEventError(f"unknown fields: {', '.join(extra)}")
    if event["schema"] != SCHEMA:
        raise AuditEventError(f"schema {event['schema']!r} is not {SCHEMA}")
    if event["type"] not in TYPES:
        raise AuditEventError(f"unknown type {event['type']!r}")
    if not isinstance(event["actor"], dict) or event["actor"].get("kind") not in ACTOR_KINDS or not event["actor"].get("id"):
        raise AuditEventError("actor needs a kind (agent, person or system) and an id")
    _walk(event, "event")
    return event
