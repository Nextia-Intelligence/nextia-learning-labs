"""ops waterfall FILE: one ticket's trace as a waterfall, with the time and the cost of each step.

    python -m ops waterfall FILE --ticket T-500123
    python -m ops waterfall FILE --slowest          the trace of the slowest ticket
    python -m ops waterfall FILE --trace 4bf92f...  one trace by its ID

Each row is a span: when it started (ms after the trace started), how long it took, a bar on
the same time scale, and the AI cost when the span is an AI call. The gap between the API's
request and the worker's job is the time the ticket waited in the queue. The summary names
the step that took the most time and the one that cost the most: you find the bottleneck
from the spans, without reading the model's mind.
"""

from ops.telemetry import Telemetry

WIDTH = 36


def register(commands) -> None:
    p = commands.add_parser("waterfall", help="one ticket's trace: time and cost of each step")
    p.add_argument("file", nargs="+", help="saved telemetry (.jsonl or .jsonl.gz)")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--ticket", help="the ticket ID, for example T-500123")
    g.add_argument("--trace", help="a trace ID")
    g.add_argument("--slowest", action="store_true", help="the sampled ticket that waited longest")
    p.add_argument("--all", action="store_true", help="also the database queries (hidden: many)")
    p.set_defaults(run=run)


def find_trace(tel: Telemetry, args) -> tuple[str | None, str]:
    traced = {s["trace_id"] for s in tel.spans}
    if args.trace:
        return args.trace, f"trace {args.trace}"
    tickets = tel.tickets()
    if args.ticket:
        t = tickets.get(args.ticket)
        if t is None:
            raise ValueError(f"no ticket {args.ticket} in the file")
        trace_id = t.get("triaged_trace") or t.get("received_trace")
        if trace_id not in traced:
            return None, f"ticket {args.ticket}"
        return trace_id, f"ticket {args.ticket}"
    sampled = [t for t in tickets.values() if t.get("triaged_trace") in traced and "triaged" in t]
    if not sampled:
        raise ValueError("no ticket in this file has a sampled trace")
    t = max(sampled, key=lambda t: t["triaged"].get("time_to_draft_s") or 0)
    return t["triaged_trace"], f"ticket {t['ticket_id']} (the slowest of {len(sampled)} sampled)"


def depth_first(spans: list[dict]) -> list[tuple[int, dict]]:
    ids = {s["span_id"] for s in spans}
    children: dict = {}
    for s in spans:
        parent = s["parent_id"] if s["parent_id"] in ids else None
        children.setdefault(parent, []).append(s)
    out = []

    def walk(parent, level):
        for s in sorted(children.get(parent, []), key=lambda s: s["start"]):
            out.append((level, s))
            walk(s["span_id"], level + 1)

    walk(None, 0)
    return out


def is_db(span: dict) -> bool:
    return span["name"].split(" ")[0] in ("SELECT", "INSERT", "UPDATE", "DELETE", "BEGIN", "COMMIT")


def run(args) -> int:
    tel = Telemetry.load(*args.file)
    trace_id, label = find_trace(tel, args)
    if trace_id is None:
        print(
            f"No trace for {label}: it was not sampled (TELEMETRY_SAMPLE keeps only some "
            "tickets' traces). Its logs are there: python -m ops trace."
        )
        return 1
    spans = [s for s in tel.spans if s["trace_id"] == trace_id]
    t0 = min(s["start"] for s in spans)
    total = (max(s["end"] for s in spans) - t0) * 1000
    print(f"Trace {trace_id}, {label}: {len(spans)} spans, {total:,.0f} ms from first to last")
    scale = WIDTH / total if total else 0
    rows, hidden = [], 0
    api_end = max((s["end"] for s in spans if s.get("service") == "ticket-api"), default=None)
    job = next((s for s in spans if s["name"] == "process ticket job"), None)
    for level, s in depth_first(spans):
        if is_db(s) and not args.all:
            hidden += 1
            continue
        if s is job and api_end is not None and job["start"] > api_end:
            wait = (job["start"] - api_end) * 1000
            rows.append(("  (waiting in the queue)", (api_end - t0) * 1000, wait, None, "-"))
        start, ms = (s["start"] - t0) * 1000, (s["end"] - s["start"]) * 1000
        cost = s["attributes"].get("app.cost_usd")
        name = "  " * level + s["name"] + (" ERROR" if s["status"] == "error" else "")
        rows.append((name, start, ms, cost, s.get("service", "")))
    width = max(len(r[0]) for r in rows)
    print(f"{'span':<{width}}  {'start ms':>9}  {'ms':>8}  {'':<{WIDTH}}  cost US$")
    for name, start, ms, cost, _service in rows:
        bar = " " * int(start * scale) + "#" * max(1, int(ms * scale))
        print(
            f"{name:<{width}}  {start:>9,.0f}  {ms:>8,.1f}  {bar[:WIDTH]:<{WIDTH}}  "
            + (f"{cost:.6f}" if cost is not None else "")
        )
    if hidden:
        print(f"({hidden} database queries hidden; --all shows them)")
    ai = [s for s in spans if "gen_ai.operation.name" in s["attributes"]]
    work = [
        s for s in spans if not is_db(s) and s["name"] != "process ticket job" and s["parent_id"]
    ]
    steps = [(s["name"], (s["end"] - s["start"]) * 1000) for s in work]
    steps += [(name.strip(), ms) for name, _, ms, _, _ in rows if name.strip().startswith("(")]
    if steps:
        name, ms = max(steps, key=lambda x: x[1])
        print(f"Longest step: {name}, {ms:,.0f} ms ({ms / total:.0%} of the trace)")
    if ai:
        dear = max(ai, key=lambda s: s["attributes"].get("app.cost_usd") or 0)
        cost = sum(s["attributes"].get("app.cost_usd") or 0 for s in ai)
        a = dear["attributes"]
        print(
            f"Costliest step: {dear['name']}, US${a.get('app.cost_usd', 0):.6f} of US${cost:.6f}: "
            f"{a.get('gen_ai.usage.input_tokens')} tokens in, "
            f"{a.get('gen_ai.usage.output_tokens')} out"
            + (
                f" ({a['gen_ai.usage.reasoning_output_tokens']} of them reasoning)"
                if a.get("gen_ai.usage.reasoning_output_tokens") is not None
                else ""
            )
            + f", finish {', '.join(a.get('gen_ai.response.finish_reasons') or ['-'])}"
        )
    return 0
