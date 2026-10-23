"""Join the model gateway's usage records with the workflow's traces (python -m obs gateway USAGE.json).

The gateway records every model call with the agent, the capability, the model that answered, tokens and cost,
and the W3C traceparent that the call carried. The workflow's `chat` spans have the same call from the inside.
The join key is the span ID inside the traceparent; the run ID (X-Run-Id) joins runs.
"""

import json
from pathlib import Path


def span_of(row: dict) -> str:
    tp = row.get("traceparent") or ""
    parts = tp.split("-")
    return parts[2] if len(parts) == 4 else ""


def join(t, usage: Path) -> list[str]:
    rows = json.loads(Path(usage).read_text())
    chats = [s for r in t.runs.values() for s in r.model_spans]
    by_span = {s.span_id: s for s in chats}
    matched = [(r, by_span[span_of(r)]) for r in rows if span_of(r) in by_span]
    g_in, g_out = sum(r.get("tokens_in") or 0 for r in rows), sum(r.get("tokens_out") or 0 for r in rows)
    a_in = sum(s.get("gen_ai.usage.input_tokens") or 0 for s in chats)
    a_out = sum(s.get("gen_ai.usage.output_tokens") or 0 for s in chats)
    g_cost = sum(r.get("cost_usd") or 0 for r in rows)
    a_cost = sum(s.get("larkfield.cost.usd") or 0 for s in chats)
    outcomes: dict = {}
    for r in rows:
        outcomes[r.get("outcome")] = outcomes.get(r.get("outcome"), 0) + 1
    tools = sum(len(r.tool_spans) for r in t.runs.values())
    waits = sum(1 for r in t.runs.values() for s in r.spans if s.name == "approval.request")
    lines = [f"Gateway records: {len(rows)} model calls ({', '.join(f'{k} {v}' for k, v in sorted(outcomes.items(), key=str))})",
             f"Workflow traces: {len(t.runs)} runs, {len(chats)} model calls, {tools} tool calls, {waits} approval requests",
             f"Joined by trace context (the span ID in traceparent): {len(matched)} of {len(rows)} records",
             f"Tokens in / out: gateway {g_in:,} / {g_out:,}; traces {a_in:,} / {a_out:,}",
             f"Cost: gateway US${g_cost:.5f}; traces US${a_cost:.5f}",
             "Only the gateway sees: the agent's registration and team, the capability, the provider, refused calls.",
             "Only the traces see: the tool calls, the approval, the outcome of the run, and which step made each call."]
    models = sorted({(r.get("capability"), f"{r.get('deployment')} ({r.get('model_version')})") for r in rows
                     if r.get("outcome") == "ok"})
    for cap, model in models:
        lines.append(f"  capability {cap} was answered by {model}")
    return lines

