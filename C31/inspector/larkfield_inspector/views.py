"""The JSON views of the inspector: rows for the Runs table, one run, cost, compare and audit.

Everything here reads runs made by vendor/obs/model.py and flags made by vendor/obs/flags.py.
The flags are not computed again here: `run.flags` comes from the same rules as `python -m obs find`.
This file only finds the spans that a flag talks about, so that the Run screen can mark them.
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from urllib.parse import quote

from .vendor.obs import flags as rules

BUDGET_PER_RESOLVED = float(os.environ.get("INSPECTOR_BUDGET_USD", "0.002"))
TZ_HOURS = float(os.environ.get("OBS_TZ_OFFSET", "-4"))   # Larkfield: Toronto, October (as the obs tool)
TZ = timezone(timedelta(hours=TZ_HOURS))


def ms(ns: int) -> int:
    return int(ns // 1_000_000)


def constructed(run) -> bool:
    return run.run_id.startswith("C-")


# ------------------------------------------------------------------ Runs

def run_row(run) -> dict:
    tin, tout = run.tokens
    return {
        "run_id": run.run_id, "ticket": run.ticket, "start": ms(run.start), "end": ms(run.end),
        "outcome": run.outcome, "proposal": run.proposal, "stop_reason": run.stop_reason,
        "model_calls": len(run.model_spans), "reads": len(run.reads), "tool_calls": len(run.tool_spans),
        "writes": len(run.writes), "replies": len(run.replies), "approvals": len(run.decisions),
        "cost": run.cost, "tokens_in": tin, "tokens_out": tout, "duration_s": round(run.duration, 3),
        "wait_s": run.wait_s, "approver": run.approver, "model": run.model, "design": run.design,
        "language": run.language, "release": run.release, "flags": sorted(run.flags),
        "traces": len(run.trace_ids), "constructed": constructed(run),
    }


def parse_time(value: str | None) -> int | None:
    """A time filter: milliseconds since 1970, or an ISO 8601 date and time. -> nanoseconds."""
    if not value:
        return None
    try:
        return int(float(value)) * 1_000_000
    except ValueError:
        pass
    t = datetime.fromisoformat(value)
    if t.tzinfo is None:
        t = t.replace(tzinfo=TZ)
    return int(t.timestamp() * 1e9)


def _float(value):
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def select_runs(runs, q: dict) -> list:
    out = list(runs)
    if q.get("outcome"):
        out = [r for r in out if r.outcome == q["outcome"]]
    flag = q.get("flag")
    if flag == "any":
        out = [r for r in out if r.flags]
    elif flag == "none":
        out = [r for r in out if not r.flags]
    elif flag:
        out = [r for r in out if flag in r.flags]
    for key, attr in (("model", "model"), ("language", "language"), ("release", "release"),
                      ("design", "design"), ("ticket", "ticket")):
        if q.get(key):
            out = [r for r in out if getattr(r, attr) == q[key]]
    lo, hi = _float(q.get("min_cost")), _float(q.get("max_cost"))
    if lo is not None:
        out = [r for r in out if r.cost >= lo]
    if hi is not None:
        out = [r for r in out if r.cost <= hi]
    start, end = parse_time(q.get("from")), parse_time(q.get("to"))
    if start is not None:
        out = [r for r in out if r.start >= start]
    if end is not None:
        out = [r for r in out if r.start < end]
    if q.get("q"):
        text = q["q"].strip().lower()
        out = [r for r in out if text in r.run_id.lower() or text in r.ticket.lower()]
    return out


def runs_view(runs: list, q: dict) -> dict:
    chosen = select_runs(runs, q)
    sort = q.get("sort", "start")
    keys = {"start": lambda r: r.start, "cost": lambda r: r.cost, "duration": lambda r: r.duration,
            "steps": lambda r: len(r.model_spans)}
    chosen.sort(key=keys.get(sort, keys["start"]), reverse=q.get("order") == "desc")
    facets = {
        "outcomes": sorted({r.outcome for r in runs}), "models": sorted({r.model for r in runs if r.model}),
        "languages": sorted({r.language for r in runs if r.language}),
        "releases": sorted({r.release for r in runs if r.release}),
        "flags": list(rules.RULES),
    }
    flag_counts = Counter(f for r in chosen for f in r.flags)
    return {"runs": [run_row(r) for r in chosen], "total": len(runs), "shown": len(chosen),
            "flagged": sum(1 for r in chosen if r.flags), "flag_counts": dict(flag_counts), "facets": facets}


# ------------------------------------------------------------------ one run

def _depth(span, by_id) -> int:
    d, p = 0, span.parent_id
    while p and p in by_id and d < 12:
        d, p = d + 1, by_id[p].parent_id
    return d


def flag_spans(run) -> dict:
    """flag name -> the span IDs that the flag's reason talks about (for marking them on the timeline)."""
    out = {}
    if "loop" in run.flags:
        asked = Counter(x for s in run.model_spans for x in (s.get("larkfield.model.requested") or [])
                        if not x.startswith("finish("))
        repeated = {x for x, n in asked.items() if n > 1}
        out["loop"] = [s.span_id for s in run.model_spans
                       if repeated & set(s.get("larkfield.model.requested") or [])]
    if "hidden_tool_error" in run.flags:
        reads = run.reads
        out["hidden_tool_error"] = [s.span_id for i, s in enumerate(reads) if s.error and not any(
            x.tool == s.tool and not x.error for x in reads[i + 1:])]
    if "duplicate_write" in run.flags:
        done = [s for s in run.writes if s.get("larkfield.write.outcome") in ("done", "timeout")
                and rules._changed(run, s)]
        groups = defaultdict(list)
        for s in done:
            groups[rules._effect(s)].append(s)
        keys = Counter(s.get("larkfield.idempotency_key") for s in done)
        out["duplicate_write"] = [s.span_id for s in done
                                  if len(groups[rules._effect(s)]) > 1 or keys[s.get("larkfield.idempotency_key")] > 1]
    if "no_action" in run.flags:
        out["no_action"] = [s.span_id for s in run.replies if s.get("larkfield.reply.status") == "failed"]
    if "followed_injection" in run.flags:
        marked = [s for s in run.spans if s.get("larkfield.input.injection")]
        first = min(marked, key=lambda s: s.start)
        writes = [w.span_id for w in run.writes if w.start >= first.start and w.get("larkfield.write.outcome") == "done"]
        out["followed_injection"] = [s.span_id for s in marked] + writes
    return out


def _kind(span) -> str:
    if span.op == "chat":
        return "model"
    if span.op == "execute_tool":
        return "write" if span.is_write else "read"
    if span.op in ("invoke_agent", "invoke_workflow"):
        return "agent"
    if span.op == "approve" or span.name.startswith("approval"):
        return "approval"
    if span.name.startswith("reconcile"):
        return "check"
    return "other"


def span_view(span, origin: int, by_id: dict) -> dict:
    a = span.attrs
    status = a.get("larkfield.write.outcome") or a.get("larkfield.reply.status") or a.get("larkfield.tool.status") or ""
    return {
        "span_id": span.span_id, "parent_id": span.parent_id, "trace_id": span.trace_id, "name": span.name,
        "kind": _kind(span), "op": span.op, "tool": span.tool, "depth": _depth(span, by_id),
        "offset_s": round((span.start - origin) / 1e9, 3), "duration_s": round(span.seconds, 3),
        "start": ms(span.start), "error": span.error, "error_type": a.get("error.type") or span.status_message,
        "status": status, "tokens_in": a.get("gen_ai.usage.input_tokens") if span.op == "chat" else None,
        "tokens_out": a.get("gen_ai.usage.output_tokens") if span.op == "chat" else None,
        "cost": a.get("larkfield.cost.usd") if span.op == "chat" else None,
        "attempt": a.get("larkfield.attempt"), "retry": (a.get("larkfield.attempt") or 1) > 1,
        "links": [{"trace_id": t, "span_id": s, "attrs": at} for t, s, at in span.links],
        "attrs": a,
    }


def links_for(trace_id: str, start_ns: int, end_ns: int, cfg: dict) -> dict:
    out = {}
    grafana = cfg.get("grafana_url")
    if grafana:
        pane = {"a": {"datasource": cfg.get("grafana_tempo_uid", "tempo"),
                      "queries": [{"refId": "A", "datasource": {"type": "tempo", "uid": cfg.get("grafana_tempo_uid", "tempo")},
                                   "queryType": "traceql", "query": trace_id}],
                      "range": {"from": str(ms(start_ns) - 3_600_000), "to": str(ms(end_ns) + 3_600_000)}}}
        out["grafana"] = (f"{grafana.rstrip('/')}/explore?schemaVersion=1&orgId=1&panes="
                          + quote(json.dumps(pane, separators=(",", ":"))))
    if cfg.get("langfuse_url"):
        out["langfuse"] = f"{cfg['langfuse_url'].rstrip('/')}/traces/{trace_id}"
    return out


def run_detail(run, cfg: dict, same_ticket: list[str], staff: dict | None = None) -> dict:
    staff = staff or {}
    by_id = {s.span_id: s for s in run.spans}
    traces, waits = [], []
    for n, trace_id in enumerate(run.trace_ids, 1):
        spans = [s for s in run.spans if s.trace_id == trace_id]
        origin = min(s.start for s in spans)
        end = max(s.end for s in spans)
        root = next((s for s in spans if not s.parent_id), spans[0])
        if n > 1:
            prev = max((s for s in run.spans if s.trace_id != trace_id and s.end <= root.start),
                       key=lambda s: s.end, default=None)
            if prev is not None:
                waits.append({
                    "before_trace": trace_id, "seconds": round((root.start - prev.end) / 1e9, 1),
                    "from": ms(prev.end), "to": ms(root.start),
                    "approver": root.get("larkfield.approval.approver", ""),
                    "approver_name": staff.get(root.get("larkfield.approval.approver", ""), {}).get("name", ""),
                    "role": root.get("larkfield.approval.role", ""),
                    "limit": root.get("larkfield.approval.limit"),
                    "decision": root.get("larkfield.approval.decision", ""),
                    "wait_s": root.get("larkfield.approval.wait_s"),
                    "link": [{"trace_id": t, "span_id": s} for t, s, _ in root.links],
                })
        traces.append({"trace_id": trace_id, "number": n, "start": ms(origin), "duration_s": round((end - origin) / 1e9, 3),
                       "root": root.name, "links": links_for(trace_id, origin, end, cfg),
                       "spans": [span_view(s, origin, by_id) for s in spans]})
    marks = flag_spans(run)
    price_tables = sorted({s.get("larkfield.price_table") for s in run.model_spans if s.get("larkfield.price_table")})
    return {
        "run": run_row(run), "traces": traces, "waits": waits,
        "flags": [{"name": k, "why": v, "spans": marks.get(k, [])} for k, v in run.flags.items()],
        "price_tables": price_tables, "same_ticket": same_ticket,
        "root": {k: v for k, v in (run.root.attrs if run.root else {}).items()},
        "service": run.spans[0].service if run.spans else "",
    }


# ------------------------------------------------------------------ cost

def _bucket_start(ns: int, bucket: str) -> datetime:
    t = datetime.fromtimestamp(ns / 1e9, TZ)
    if bucket == "hour":
        return t.replace(minute=0, second=0, microsecond=0)
    return t.replace(hour=0, minute=0, second=0, microsecond=0)


def _group(rs: list) -> dict:
    cost = sum(r.cost for r in rs)
    resolved = sum(1 for r in rs if r.outcome == "resolved")
    return {"runs": len(rs), "resolved": resolved, "cost": round(cost, 8),
            "per_run": round(cost / len(rs), 8) if rs else None,
            "per_resolved": round(cost / resolved, 8) if resolved else None,
            "success": round(resolved / len(rs), 4) if rs else None}


def cost_view(runs: list, q: dict) -> dict:
    bucket = "hour" if q.get("bucket") == "hour" else "day"
    chosen = select_runs(runs, {k: q.get(k) for k in ("model", "language", "outcome", "release")})
    series = []
    if runs:
        step = timedelta(hours=1) if bucket == "hour" else timedelta(days=1)
        first = _bucket_start(min(r.start for r in runs), bucket)
        last = _bucket_start(max(r.start for r in runs), bucket)
        by_bucket = defaultdict(list)
        for r in chosen:
            by_bucket[_bucket_start(r.start, bucket)].append(r)
        t = first
        while t <= last:
            row = _group(by_bucket.get(t, []))
            models = Counter(r.model for r in by_bucket.get(t, []))
            row.update({"start": int(t.timestamp() * 1000), "end": int((t + step).timestamp() * 1000),
                        "models": dict(models)})
            series.append(row)
            t += step
    groups = {}
    for name, key in (("model", lambda r: r.model), ("language", lambda r: r.language),
                      ("outcome", lambda r: r.outcome), ("release", lambda r: r.release)):
        g = defaultdict(list)
        for r in chosen:
            g[key(r)].append(r)
        groups[name] = [{"key": k, **_group(v)} for k, v in sorted(g.items(), key=lambda kv: str(kv[0]))]
    steps = defaultdict(lambda: {"calls": 0, "cost": 0.0, "tokens_in": 0, "tokens_out": 0})
    for r in chosen:
        for s in r.model_spans:
            row = steps[(s.get("gen_ai.request.model") or "", s.get("larkfield.step") or 0)]
            row["calls"] += 1
            row["cost"] += s.get("larkfield.cost.usd") or 0
            row["tokens_in"] += s.get("gen_ai.usage.input_tokens") or 0
            row["tokens_out"] += s.get("gen_ai.usage.output_tokens") or 0
    step_rows = [{"model": m, "step": st, **v, "cost": round(v["cost"], 8)} for (m, st), v in sorted(steps.items())]
    releases = []
    for r in sorted(runs, key=lambda r: r.start):
        if r.release and r.release not in [x["release"] for x in releases]:
            releases.append({"release": r.release, "first_run": ms(r.start), "run_id": r.run_id})
    tables = Counter(s.get("larkfield.price_table") for r in chosen for s in r.model_spans
                     if s.get("larkfield.price_table"))
    top = sorted(chosen, key=lambda r: r.cost, reverse=True)[:10]
    return {"bucket": bucket, "series": series, "total": _group(chosen), "groups": groups, "steps": step_rows,
            "top": [run_row(r) for r in top], "budget_per_resolved": BUDGET_PER_RESOLVED,
            "price_tables": [{"date": k, "model_calls": n} for k, n in sorted(tables.items())],
            "releases": releases, "tz_hours": TZ_HOURS}


# ------------------------------------------------------------------ compare

def steps_of(run) -> list[dict]:
    """The run as a list of steps: model decisions, tool results and approvals (the agent span is left out)."""
    out = []
    for s in run.spans:
        a = s.attrs
        if s.op == "chat":
            requested = a.get("larkfield.model.requested") or []
            finish = any(x.startswith("finish(") for x in requested)
            names = [x.split("(")[0] for x in requested]
            value = {"requested": names, "error": s.error}
            if finish:
                value.update({"proposal": run.proposal, "rule": run.attr("larkfield.proposal.rule", "")})
            out.append({"kind": "model", "sig": "model", "value": value, "span_id": s.span_id,
                        "name": s.name, "requested": requested, "cost": a.get("larkfield.cost.usd"),
                        "tokens_in": a.get("gen_ai.usage.input_tokens"), "tokens_out": a.get("gen_ai.usage.output_tokens")})
        elif s.op == "execute_tool":
            status = a.get("larkfield.write.outcome") or a.get("larkfield.reply.status") or a.get("larkfield.tool.status") or ""
            value = {"status": status, "error": s.error, "amount": a.get("larkfield.refund.amount"),
                     "quantity": a.get("larkfield.quantity")}
            out.append({"kind": "tool", "sig": f"tool:{s.tool}", "value": value, "span_id": s.span_id, "name": s.name,
                        "tool": s.tool, "tool_kind": a.get("larkfield.tool.kind"), "order": a.get("larkfield.order.id"),
                        "attempt": a.get("larkfield.attempt"), "key": a.get("larkfield.idempotency_key")})
        elif s.name == "approval.request":
            value = {"needs_role": a.get("larkfield.approval.needs_role"), "limit": a.get("larkfield.approval.limit")}
            out.append({"kind": "approval", "sig": "approval_request", "value": value, "span_id": s.span_id, "name": s.name})
        elif s.op == "approve":
            value = {"decision": a.get("larkfield.approval.decision"), "approver": a.get("larkfield.approval.approver"),
                     "role": a.get("larkfield.approval.role"), "limit": a.get("larkfield.approval.limit")}
            out.append({"kind": "approval", "sig": "approval", "value": value, "span_id": s.span_id, "name": s.name,
                        "wait_s": a.get("larkfield.approval.wait_s")})
        elif s.name.startswith("reconcile"):
            value = {"found": a.get("larkfield.reconcile.found")}
            out.append({"kind": "tool", "sig": f"check:{s.name}", "value": value, "span_id": s.span_id, "name": s.name})
    for i, st in enumerate(out, 1):
        st["index"] = i
    return out


DIFF_KIND = {"model": "model_decision", "tool": "tool_result", "approval": "approval"}


def compare_view(a, b) -> dict:
    sa, sb = steps_of(a), steps_of(b)
    rows = []
    matcher = SequenceMatcher(a=[x["sig"] for x in sa], b=[x["sig"] for x in sb], autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for x, y in zip(sa[i1:i2], sb[j1:j2]):
                rows.append({"a": x, "b": y, "same": x["value"] == y["value"]})
        else:
            left, right = sa[i1:i2], sb[j1:j2]
            for k in range(max(len(left), len(right))):
                x = left[k] if k < len(left) else None
                y = right[k] if k < len(right) else None
                same = bool(x and y and x["sig"] == y["sig"] and x["value"] == y["value"])
                rows.append({"a": x, "b": y, "same": same})
    first = None
    for i, row in enumerate(rows):
        if not row["same"]:
            step = row["a"] or row["b"]
            kind = DIFF_KIND[step["kind"]]
            if row["a"] and row["b"] and row["a"]["kind"] != row["b"]["kind"]:
                kind = DIFF_KIND[row["a"]["kind"]]
            first = {"row": i, "kind": kind, "a": row["a"], "b": row["b"]}
            break
    return {"a": run_row(a), "b": run_row(b), "same_ticket": a.ticket == b.ticket, "rows": rows,
            "first_difference": first}


def default_compare(runs: dict) -> tuple[str, str] | None:
    """Two runs of one ticket to show first: the double refund and the small model's run, if they are there."""
    if "R-1014-040" in runs and "R-1012-034" in runs:
        return "R-1014-040", "R-1012-034"
    by_ticket = defaultdict(list)
    for r in runs.values():
        by_ticket[r.ticket].append(r)
    for r in runs.values():
        if r.flags and len(by_ticket[r.ticket]) > 1:
            other = next(x for x in by_ticket[r.ticket] if x.run_id != r.run_id)
            return r.run_id, other.run_id
    for rs in by_ticket.values():
        if len(rs) > 1:
            return rs[0].run_id, rs[1].run_id
    return None


# ------------------------------------------------------------------ audit

def audit_view(records: list[dict], verified: dict, run_id: str, staff: dict, sentence) -> dict:
    """The audit records of one run, with the facts that the Audit screen tells as a story."""
    seq_of = {r["event"]["event_id"]: r["seq"] for r in records}
    by_seq = {r["seq"]: r for r in records}
    mine = [r for r in records if r["event"]["run_id"] == run_id]
    out_records = []
    for r in mine:
        e = r["event"]
        actor = dict(e["actor"])
        if actor.get("kind") == "person" and actor["id"] in staff:
            actor["name"] = staff[actor["id"]].get("name")
            actor["title"] = staff[actor["id"]].get("title")
        prev_rec = by_seq.get(r["seq"] - 1)
        out_records.append({
            "seq": r["seq"], "at": e["at"], "type": e["type"], "actor": actor, "action": e["action"],
            "authority": e["authority"], "evidence": e.get("evidence") or [], "subject": e["subject"],
            "trace_id": e.get("trace_id"), "span_id": e.get("span_id"), "hash": r["hash"], "prev": r["prev"],
            "links_ok": (prev_rec["hash"] if prev_rec else "0" * 64) == r["prev"],
            "sentence": sentence(e, staff, seq_of),
            "refers_to": {"proposal": seq_of.get(e["action"].get("proposal_event_id")),
                          "approval": seq_of.get(e["authority"].get("approval_event_id"))},
        })
    events = [r["event"] for r in mine]
    writes = [e for e in events if e["type"] == "write"]
    changes = {}
    for w in writes:
        if w["action"]["outcome"] not in ("done", "timeout"):
            continue
        key = json.dumps(w["action"]["effect"], sort_keys=True)
        c = changes.setdefault(key, {"effect": w["action"]["effect"], "calls": 0, "outcomes": [], "keys": []})
        c["calls"] += 1
        c["outcomes"].append(w["action"]["outcome"])
        if w["action"]["idempotency_key"] not in c["keys"]:
            c["keys"].append(w["action"]["idempotency_key"])
    customers = sorted({e["subject"].get("customer") for e in events if e["subject"].get("customer")})
    reads = [e["action"] | {"seq": r["seq"]} for r, e in zip(mine, events) if e["type"] == "data_access"]
    evidence = sorted({x for e in events for x in (e.get("evidence") or [])})
    return {
        "run_id": run_id, "ticket": events[0]["ticket_id"] if events else "", "records": out_records,
        "verify": verified, "customers": customers, "reads": reads, "evidence": evidence,
        "orders": sorted({x.split(":", 1)[1] for x in evidence if x.startswith("order:")}),
        "passages": sorted({x.split(":", 1)[1] for x in evidence if x.startswith("passage:")}),
        "changes": list(changes.values()), "writes": len(writes),
        "approvals": sum(1 for e in events if e["type"] == "approval"),
        "trace_ids": sorted({e["trace_id"] for e in events if e.get("trace_id")}),
    }
