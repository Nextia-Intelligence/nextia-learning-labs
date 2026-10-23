"""The audit story of one run: the trail told in plain sentences, for a person outside engineering.

It uses the audit trail only (not the traces), so it shows what the trail can answer and what it cannot.
`--markdown` gives the same story as a Markdown document for an auditor.
"""

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
ROLE_WORDS = {"agent": "support agent", "team_lead": "team lead", "grace": "support lead"}


def people() -> dict:
    path = PROJECT / "data" / "people.json"
    return json.loads(path.read_text(encoding="utf-8"))["people"] if path.exists() else {}


def _time(at: str, tz_hours: float = -4) -> str:
    t = datetime.fromisoformat(at).astimezone(timezone(timedelta(hours=tz_hours)))
    return t.strftime("%a %d %b %H:%M:%S")


def _effect(e: dict) -> str:
    tool = e.get("tool", "")
    if tool == "request_refund":
        return f"refund {e.get('amount', 0):.2f} ({e.get('reason_code')}) on {e.get('order_id')}"
    if tool == "reship_item":
        return f"reship {e.get('sku')} x {e.get('quantity')} on {e.get('order_id')}"
    if tool == "create_return_label":
        return f"return label for {e.get('sku')} ({e.get('label_reason')}) on {e.get('order_id')}"
    return f"{tool} on {e.get('order_id')}"


def _who(actor: dict, staff: dict) -> str:
    if actor["kind"] == "person":
        p = staff.get(actor["id"], {})
        name = p.get("name", actor["id"])
        return f"{name} ({actor['id']}, {ROLE_WORDS.get(actor.get('role'), actor.get('role', ''))})"
    if actor["kind"] == "agent":
        return f"The AI agent {actor['id']} ({actor.get('model', '')}, {actor.get('role', '')})"
    return f"The workflow ({actor['id']})"


def sentence(e: dict, staff: dict, seq_of: dict) -> str:
    a, who = e["action"], _who(e["actor"], staff)
    t = e["type"]
    if t == "data_access":
        orders = ", ".join(a.get("orders") or []) or e["subject"].get("order_id", "")
        return f"{who} read {a['tool']}" + (f" ({orders})" if orders else "") + f": {a['status']}."
    if t == "proposal":
        acts = "; ".join(_effect(x) for x in a.get("actions") or []) or "no change"
        need = e["authority"].get("needs_role")
        ev = ", ".join(e.get("evidence") or []) or "none"
        return (f"{who} proposed: {a['outcome']} (rule {a['rule']}): {acts}."
                + (f" It needs a {ROLE_WORDS.get(need, need)} or above to approve." if need else "")
                + f" Evidence it read: {ev}.")
    if t in ("approval", "refusal"):
        lim = e["authority"].get("limit")
        lim = "no limit" if lim in (-1, None) else f"limit {lim:g}"
        prop = seq_of.get(a.get("proposal_event_id"), "?")
        wait = a.get("wait_s")
        waited = ""
        if wait:
            h, m = int(wait // 3600), int(wait % 3600 // 60)
            waited = f" after {h} h {m:02d} min" if h else f" after {m} min"
        if a.get("decision") == "refused_by_rules":
            return f"{who} tried to approve the proposal of record {prop}; the rules refused it ({lim}, it needs a " \
                   f"{ROLE_WORDS.get(e['authority'].get('needs_role'), '')})."
        return f"{who} {a['decision']} the proposal of record {prop}{waited} ({lim})."
    if t == "write":
        auth = seq_of.get(e["authority"].get("approval_event_id"), "none")
        return (f"{who} sent {_effect(a.get('effect') or {})}: {a['outcome'].upper() if a['outcome'] != 'done' else 'done'} "
                f"(attempt {a.get('attempt')}, key {a.get('idempotency_key')}). Authority: the approval of record {auth}.")
    if t == "handoff":
        return f"{who} handed the ticket to {a.get('to')} ({a.get('code')})."
    if t == "run_closed":
        return f"The ticket was closed: {a['outcome'].replace('_', ' ')} (writes done: {a.get('writes_done')}, " \
               f"reply: {a.get('reply_status')})."
    return f"{t}: {json.dumps(a)}"


def story(store, target: str | None, markdown: bool = False, data: Path | None = None) -> str:
    staff = people()
    records = store.records()
    if target:
        mine = [r for r in records if target in (r["event"]["run_id"], r["event"]["ticket_id"])]
        runs = sorted({r["event"]["run_id"] for r in mine})
        if len(runs) > 1 and target not in runs:
            last = mine[-1]["event"]["run_id"]
            mine = [r for r in mine if r["event"]["run_id"] == last]
    else:
        mine = records
    if not mine:
        return f"No audit records for {target}."
    seq_of = {r["event"]["event_id"]: r["seq"] for r in records}
    v = store.verify()
    e0 = mine[0]["event"]
    head = (f"Audit story of ticket {e0['ticket_id']}, run {e0['run_id']}: {len(mine)} records "
            f"({'the trail verifies' if v['ok'] else 'THE TRAIL DOES NOT VERIFY: ' + '; '.join(v['problems'])}).")
    lines = [head, ""]
    for r in mine:
        e = r["event"]
        lines.append(f"{r['seq']:>5}. {_time(e['at'])}  {sentence(e, staff, seq_of)}")
    writes = [r["event"] for r in mine if r["event"]["type"] == "write"]
    approvals = [r["event"] for r in mine if r["event"]["type"] == "approval"]
    if writes:
        effects = Counter(json.dumps(w["action"]["effect"], sort_keys=True) for w in writes
                          if w["action"]["outcome"] in ("done", "timeout"))
        lines.append("")
        lines.append(f"Changes asked of the systems: {len(writes)} write call(s) after {len(approvals)} approval(s).")
        for effect, n in effects.items():
            e = json.loads(effect)
            outcomes = [w["action"]["outcome"] for w in writes if json.dumps(w["action"]["effect"], sort_keys=True) == effect]
            keys = sorted({w["action"]["idempotency_key"] for w in writes if json.dumps(w["action"]["effect"], sort_keys=True) == effect})
            lines.append(f"  {_effect(e)}: {n} call(s) that may have changed it ({', '.join(outcomes)}), "
                         f"{len(keys)} different key(s)")
    if markdown:
        md = [f"# Audit story: ticket {e0['ticket_id']}", "", f"Run `{e0['run_id']}`. {head.split(': ', 1)[1]}", "",
              "| # | Time (Toronto) | What happened |", "|---|---|---|"]
        for r in mine:
            md.append(f"| {r['seq']} | {_time(r['event']['at'])} | {sentence(r['event'], staff, seq_of)} |")
        tail = [("- " + x.strip()) if x.startswith("  ") else x for x in lines[len(mine) + 2:] if x.strip()]
        md += ["", *tail, "",
               "Source: the audit store (append-only, hash-chained). The trace IDs of each record are in the store."]
        return "\n".join(md)
    return "\n".join(lines)
