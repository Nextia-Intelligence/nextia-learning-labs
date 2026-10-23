"""obs: read the workflow's saved telemetry and audit trail from the command line (no Docker, no account).

    python -m obs runs   [--data DIR] [--outcome X] [--flag F] [--model M] [--language L] [--day D] [--limit N]
    python -m obs trace  RUN_ID|TICKET|TRACE_ID [--data DIR]
    python -m obs find   loop|hidden_tool_error|duplicate_write|no_action|followed_injection|all [--data DIR]
    python -m obs find   --tool get_order --min-calls 3 | --write-without-approval | --error-then-resolved
    python -m obs cost   [--by model|language|outcome|design|day|step|customer|release] [--data DIR]
    python -m obs events [RUN_ID] [--name larkfield.run.closed] [--data DIR]
    python -m obs audit  verify|show RUN_ID|story RUN_ID|forget CUSTOMER_ID [--audit FILE] [--markdown]
    python -m obs slo    [--data DIR] [--window 45]
    python -m obs alerts [--data DIR] [--rules grafana/alerts/rules.json] [--min-runs N]
    python -m obs reviews [--by language|model|release|outcome|day] [--failed] [--queue [--share 0.2] [--every de,fr]]
    python -m obs check-redaction DIR
    python -m obs gateway USAGE.json [--data DIR]

DIR defaults to your own runs (work/telemetry, or OBS_TELEMETRY). The course's replayed week is in
data/telemetry/week (and data/telemetry/healthy-week).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .model import Telemetry

PROJECT = Path(__file__).resolve().parent.parent
WORK = Path(os.environ.get("RESOLVER_WORK", PROJECT / "work"))
TZ = timezone(timedelta(hours=float(os.environ.get("OBS_TZ_OFFSET", "-4"))))   # Larkfield: Toronto, October


def when(ns: int, fmt: str = "%a %d %b %H:%M:%S") -> str:
    return datetime.fromtimestamp(ns / 1e9, TZ).strftime(fmt)


def money(x) -> str:
    return "-" if x is None else f"US${x:.5f}"


def default_data() -> Path:
    return Path(os.environ.get("OBS_TELEMETRY", WORK / "telemetry"))


def load(args) -> Telemetry:
    folder = Path(args.data) if getattr(args, "data", None) else default_data()
    if not (folder / "traces.jsonl").exists() and not (folder / "traces.jsonl.gz").exists():
        sys.exit(f"No telemetry in {folder}. Run a ticket first (python -m resolver run T-80008), "
                 "or read the replayed week: --data data/telemetry/week")
    return Telemetry(folder)


# ------------------------------------------------------------------ runs

def run_row(r, w: int = 26) -> str:
    flags = ",".join(sorted(r.flags)) or "-"
    return (f"{r.run_id:<{w}} {r.ticket:<8} {when(r.start, '%a %H:%M'):<9} {r.outcome:<17} {len(r.model_spans):>5} "
            f"{len(r.reads):>5} {len(r.decisions):>4} {r.cost:>9.5f} {r.duration:>6.1f} {r.model:<11} {flags}")


def select(t: Telemetry, args) -> list:
    runs = list(t.runs.values())
    if getattr(args, "outcome", None):
        runs = [r for r in runs if r.outcome == args.outcome]
    if getattr(args, "flag", None):
        runs = [r for r in runs if args.flag in r.flags]
    if getattr(args, "model", None):
        runs = [r for r in runs if r.model == args.model]
    if getattr(args, "language", None):
        runs = [r for r in runs if r.language == args.language]
    if getattr(args, "day", None):
        runs = [r for r in runs if when(r.start, "%a").lower().startswith(args.day.lower()[:3])]
    if getattr(args, "release", None):
        runs = [r for r in runs if r.release == args.release]
    return runs


def cmd_runs(args):
    t = load(args)
    runs = select(t, args)
    w = max([len(r.run_id) for r in runs] + [12])
    print(f"{'run':<{w}} {'ticket':<8} {'started':<9} {'outcome':<17} {'model':>5} {'tools':>5} {'appr':>4} "
          f"{'cost US$':>9} {'secs':>6} {'model':<11} flags")
    shown = runs if not args.limit else runs[-args.limit:]
    for r in shown:
        print(run_row(r, w))
    flagged = sum(1 for r in runs if r.flags)
    print(f"{len(runs)} run(s), {flagged} flagged" + (f" (last {len(shown)} shown)" if len(shown) < len(runs) else ""))


# ------------------------------------------------------------------ one run as a waterfall

def bar(span, origin: int, total: float, width: int = 24) -> str:
    if total <= 0:
        return " " * width
    a = int((span.start - origin) / 1e9 / total * width)
    b = max(a + 1, int((span.end - origin) / 1e9 / total * width + 0.5))
    a, b = min(a, width - 1), min(b, width)
    return " " * a + "=" * (b - a) + " " * (width - b)


def describe(s) -> str:
    a = s.attrs
    if s.op == "chat":
        out = f"{a.get('gen_ai.usage.input_tokens', 0)} in / {a.get('gen_ai.usage.output_tokens', 0)} out  " \
              f"{money(a.get('larkfield.cost.usd'))}"
        if a.get("gen_ai.response.finish_reasons"):
            out += f"  {','.join(a['gen_ai.response.finish_reasons'])}"
        if s.error:
            out = f"ERROR {a.get('error.type', s.status_message)}"
        return out
    if s.op == "execute_tool":
        status = a.get("larkfield.write.outcome") or a.get("larkfield.reply.status") or a.get("larkfield.tool.status", "")
        bits = [("ERROR " if s.error else "") + str(status)]
        if a.get("larkfield.order.id"):
            bits.append(a["larkfield.order.id"])
        if a.get("larkfield.refund.amount") is not None:
            bits.append(f"{a['larkfield.refund.amount']:.2f} {a.get('larkfield.refund.reason', '')}")
        if a.get("larkfield.sku") and s.tool != "get_order":
            bits.append(f"{a['larkfield.sku']}" + (f" x {a['larkfield.quantity']}" if a.get("larkfield.quantity") else ""))
        if a.get("larkfield.idempotency_key"):
            bits.append(f"key {a['larkfield.idempotency_key']}")
        if a.get("larkfield.input.injection"):
            bits.append(f"INJECTED: {a.get('larkfield.input.injection_ask')}")
        return "  ".join(bits)
    if s.name.startswith("reconcile"):
        return "found: it happened" if a.get("larkfield.reconcile.found") else "not found"
    if s.op in ("invoke_agent", "invoke_workflow"):
        bits = [a.get("larkfield.proposal.outcome") or a.get("larkfield.stop_reason") or ""]
        if a.get("larkfield.proposal.rule"):
            bits.append(f"rule {a['larkfield.proposal.rule']}")
        if a.get("larkfield.handoff.context"):
            bits.append(f"handoff context {a['larkfield.handoff.context']}")
        return "  ".join(b for b in bits if b)
    if s.name == "approval.request":
        return f"needs {a.get('larkfield.approval.needs_role', '').replace('_', ' ')}"
    if s.op == "approve":
        lim = a.get("larkfield.approval.limit")
        return (f"{a.get('larkfield.approval.decision', '')} by {a.get('larkfield.approval.approver')} "
                f"({a.get('larkfield.approval.role', '').replace('_', ' ')}, limit "
                f"{'none' if lim == -1 else f'{lim:g}'})")
    return ""


def depth_of(span, by_id) -> int:
    d, p = 0, span.parent_id
    while p and p in by_id and d < 10:
        d, p = d + 1, by_id[p].parent_id
    return d


def waiting(seconds: float) -> str:
    h, m = int(seconds // 3600), int(seconds % 3600 // 60)
    return f"{h} h {m:02d} min" if h else f"{m} min {int(seconds % 60):02d} s"


def render_run(r) -> str:
    out = []
    tin, tout = r.tokens
    out.append(f"Run {r.run_id} | ticket {r.ticket} | {r.model} ({r.design}) | release {r.release} | "
               f"language {r.language}")
    out.append(f"{len(r.model_spans)} model call(s), {len(r.reads)} read(s), {len(r.writes)} write call(s), "
               f"{tin} tokens in, {tout} out, {money(r.cost)}")
    by_id = {s.span_id: s for s in r.spans}
    for n, trace_id in enumerate(r.trace_ids, 1):
        spans = [s for s in r.spans if s.trace_id == trace_id]
        origin = min(s.start for s in spans)
        total = max(s.end for s in spans) - origin
        out.append("")
        root = next((s for s in spans if not s.parent_id), spans[0])
        if root.links:
            prev = max((s for s in r.spans if s.trace_id != trace_id and s.end <= root.start), key=lambda s: s.end,
                       default=None)
            if prev is not None:
                out.append(f"... waited {waiting((root.start - prev.end) / 1e9)} for a person "
                           f"(this trace has a link to {root.links[0][1]} in trace {root.links[0][0][:8]}...)")
        out.append(f"Trace {n} {trace_id}  {when(origin)}  {total / 1e9:.1f} s")
        for s in spans:
            indent = "  " * depth_of(s, by_id)
            out.append(f"  {(s.start - origin) / 1e9:>6.1f} s |{bar(s, origin, total / 1e9)}| {s.seconds:>6.2f} s  "
                       f"{indent}{s.name}  {describe(s)}".rstrip())
    out.append("")
    out.append(f"Outcome: {r.outcome}" + (f" | stopped: {r.stop_reason}" if r.stop_reason not in ("", "finished") else ""))
    for name, why in r.flags.items():
        out.append(f"Flag {name}: {why}")
    return "\n".join(out)


def cmd_trace(args):
    t = load(args)
    r = t.find(args.run)
    if r is None:
        sys.exit(f"No run {args.run} in {t.folder}. List them with: python -m obs runs")
    print(render_run(r))


# ------------------------------------------------------------------ events

def cmd_events(args):
    t = load(args)
    events = t.events()
    if args.run:
        events = [e for e in events if e["attrs"].get("larkfield.run.id") == args.run]
    if args.name:
        events = [e for e in events if e["name"] == args.name]
    for e in events[-(args.limit or len(events)):]:
        attrs = {k.replace("larkfield.", ""): v for k, v in e["attrs"].items()}
        print(f"{when(e['time'])}  {e['name']:<28} trace {e['trace_id'][:8] or '-':<8} {json.dumps(attrs, ensure_ascii=False)}")
    print(f"{len(events)} event(s)")


# ------------------------------------------------------------------ audit

def audit_path(args) -> Path:
    if args.audit:
        return Path(args.audit)
    if getattr(args, "data", None):
        return Path(args.data) / "audit.jsonl"
    return Path(os.environ.get("OBS_AUDIT", WORK / "audit" / "audit.jsonl"))


def cmd_audit(args):
    sys.path.insert(0, str(PROJECT))
    from auditstore.store import AuditStore
    store = AuditStore(audit_path(args))
    if not store.path.exists():
        sys.exit(f"No audit trail at {store.path}.")
    if args.action == "verify":
        v = store.verify()
        if v["ok"]:
            print(f"The audit trail is intact: {v['count']} records, the chain and the anchor match "
                  f"(head {v['head'][:16]}).")
        else:
            print(f"The audit trail does NOT verify ({v['count']} records read):")
            for p in v["problems"]:
                print(f"  {p}")
            sys.exit(1)


def cmd_check_redaction(args):
    from .redaction import check_folder
    problems, counted = check_folder(Path(args.folder))
    print(f"Checked {counted['spans']} span(s), {counted['logs']} event(s), {counted['metrics']} metric line(s) "
          f"in {args.folder}.")
    if problems:
        print(f"{len(problems)} problem(s): text that must not leave the application:")
        for p in problems[:20]:
            print(f"  {p}")
        sys.exit(1)
    print("No text attribute, no e-mail address and no card number found.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m obs", description="Read the workflow's saved telemetry.")
    sub = ap.add_subparsers(dest="command", required=True)

    def data(p):
        p.add_argument("--data", help="a folder of saved telemetry (default: your own runs)")
        return p

    p = data(sub.add_parser("runs"))
    for f in ("outcome", "flag", "model", "language", "day", "release"):
        p.add_argument(f"--{f}")
    p.add_argument("--limit", type=int)
    p = data(sub.add_parser("trace"))
    p.add_argument("run")
    p = data(sub.add_parser("events"))
    p.add_argument("run", nargs="?")
    p.add_argument("--name")
    p.add_argument("--limit", type=int)
    p = data(sub.add_parser("audit"))
    p.add_argument("action", choices=["verify"])
    p.add_argument("target", nargs="?")
    p.add_argument("--audit", help="the audit store file (default: work/audit/audit.jsonl, or DIR/audit.jsonl)")
    p.add_argument("--markdown", action="store_true")
    p = sub.add_parser("check-redaction")
    p.add_argument("folder")
    args = ap.parse_args(argv)
    commands = {"runs": cmd_runs, "trace": cmd_trace, "events": cmd_events, "audit": cmd_audit}
    commands["check-redaction"] = cmd_check_redaction
    commands[args.command](args)


if __name__ == "__main__":
    main()
