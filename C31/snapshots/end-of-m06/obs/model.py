"""Read saved telemetry (OTLP JSON files) into spans and runs. Standard library only.

A folder of telemetry has the files that the workflow writes in file mode, or that the Collector's file
exporter writes (one OTLP export request per line, plain or gzip):

    traces.jsonl[.gz]    spans          metrics.jsonl[.gz]   metric points       logs.jsonl[.gz]   events

A RUN is everything recorded for one larkfield.run.id: trace 1 (the run until its proposal) and, when the
proposal waited for a person, trace 2 (the decision, the writes and the reply), joined by a span link.
"""

import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path

RUN_ID = "larkfield.run.id"
KINDS = {1: "internal", 2: "server", 3: "client", 4: "producer", 5: "consumer"}


def _value(v: dict):
    if "stringValue" in v:
        return v["stringValue"]
    if "intValue" in v:
        return int(v["intValue"])
    if "doubleValue" in v:
        return float(v["doubleValue"])
    if "boolValue" in v:
        return bool(v["boolValue"])
    if "arrayValue" in v:
        return [_value(x) for x in v["arrayValue"].get("values", [])]
    if "kvlistValue" in v:
        return {x["key"]: _value(x["value"]) for x in v["kvlistValue"].get("values", [])}
    return None


def attributes(items) -> dict:
    return {a["key"]: _value(a.get("value", {})) for a in items or []}


def lines(path: Path):
    """The JSON objects of a .jsonl or .jsonl.gz file (nothing if it does not exist)."""
    for p in (path, path.with_name(path.name + ".gz")):
        if p.exists():
            opener = gzip.open if p.suffix == ".gz" else open
            with opener(p, "rt", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)
            return


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: str
    name: str
    kind: str
    start: int
    end: int
    attrs: dict
    status: str = ""          # "", "ok" or "error"
    status_message: str = ""
    links: list = field(default_factory=list)   # [(trace_id, span_id, attrs)]
    service: str = ""

    @property
    def seconds(self) -> float:
        return max(0, self.end - self.start) / 1e9

    @property
    def error(self) -> bool:
        return self.status == "error"

    def get(self, key, default=None):
        return self.attrs.get(key, default)

    @property
    def op(self) -> str:
        return self.attrs.get("gen_ai.operation.name", "")

    @property
    def tool(self) -> str:
        return self.attrs.get("gen_ai.tool.name", "")

    @property
    def is_write(self) -> bool:
        return self.op == "execute_tool" and self.attrs.get("larkfield.tool.kind") == "write"

    @property
    def is_read(self) -> bool:
        return self.op == "execute_tool" and self.attrs.get("larkfield.tool.kind") == "read"


def load_spans(folder: Path) -> list[Span]:
    spans = []
    for request in lines(Path(folder) / "traces.jsonl"):
        for rs in request.get("resourceSpans", []):
            service = attributes(rs.get("resource", {}).get("attributes")).get("service.name", "")
            for ss in rs.get("scopeSpans", []):
                for s in ss.get("spans", []):
                    status = s.get("status", {}).get("code", "")
                    status = {1: "STATUS_CODE_OK", 2: "STATUS_CODE_ERROR"}.get(status, status)  # numbers or names
                    kind = s.get("kind", "")
                    kind = KINDS.get(kind, "") if isinstance(kind, int) else kind.replace("SPAN_KIND_", "").lower()
                    spans.append(Span(
                        trace_id=s["traceId"], span_id=s["spanId"], parent_id=s.get("parentSpanId", ""),
                        name=s["name"], kind=kind,
                        start=int(s["startTimeUnixNano"]), end=int(s["endTimeUnixNano"]),
                        attrs=attributes(s.get("attributes")),
                        status={"STATUS_CODE_ERROR": "error", "STATUS_CODE_OK": "ok"}.get(status, ""),
                        status_message=s.get("status", {}).get("message", ""),
                        links=[(link["traceId"], link["spanId"], attributes(link.get("attributes")))
                               for link in s.get("links", [])],
                        service=service))
    return spans


def load_events(folder: Path) -> list[dict]:
    out = []
    for request in lines(Path(folder) / "logs.jsonl"):
        for rl in request.get("resourceLogs", []):
            for sl in rl.get("scopeLogs", []):
                for r in sl.get("logRecords", []):
                    out.append({"time": int(r.get("timeUnixNano") or r.get("observedTimeUnixNano") or 0),
                                "name": r.get("eventName", ""), "attrs": attributes(r.get("attributes")),
                                "trace_id": r.get("traceId", ""), "span_id": r.get("spanId", ""),
                                "body": _value(r.get("body", {})) if r.get("body") else None})
    return sorted(out, key=lambda e: e["time"])


@dataclass
class Run:
    run_id: str
    spans: list[Span]                     # both traces, in time order
    flags: dict = field(default_factory=dict)   # flag name -> why

    def _first(self, pred):
        return next((s for s in self.spans if pred(s)), None)

    @property
    def root(self) -> Span | None:
        """Trace 1's root: the agent run (or the workflow)."""
        return self._first(lambda s: not s.parent_id and s.op in ("invoke_agent", "invoke_workflow"))

    @property
    def decision(self) -> Span | None:
        """Trace 2's root: a person's decision (approve / reject), linked to trace 1."""
        return self._first(lambda s: not s.parent_id and s.op == "approve")

    @property
    def decisions(self) -> list[Span]:
        return [s for s in self.spans if not s.parent_id and s.op == "approve"]

    @property
    def trace_ids(self) -> list[str]:
        out = []
        for s in self.spans:
            if s.trace_id not in out:
                out.append(s.trace_id)
        return out

    def attr(self, key, default=None):
        r = self.root
        return r.get(key, default) if r else default

    @property
    def ticket(self) -> str:
        return self.attr("larkfield.ticket.id", "")

    @property
    def start(self) -> int:
        return self.spans[0].start if self.spans else 0

    @property
    def end(self) -> int:
        return max(s.end for s in self.spans) if self.spans else 0

    @property
    def model(self) -> str:
        return self.attr("gen_ai.request.model", "")

    @property
    def design(self) -> str:
        return self.attr("larkfield.design", "")

    @property
    def language(self) -> str:
        return self.attr("larkfield.ticket.language", "")

    @property
    def release(self) -> str:
        return self.attr("larkfield.release", "")

    @property
    def customer(self) -> str:
        return self.attr("larkfield.customer.id", "")

    @property
    def outcome(self) -> str:
        """The ticket's final outcome (set where the run was closed), or waiting_approval."""
        for s in reversed(self.spans):
            if s.get("larkfield.outcome"):
                return s.get("larkfield.outcome")
        r = self.root
        if r is not None and r.get("larkfield.status") == "waiting_approval":
            return "waiting_approval"
        return "unknown"

    @property
    def proposal(self) -> str:
        return self.attr("larkfield.proposal.outcome", "") or ""

    @property
    def stop_reason(self) -> str:
        return self.attr("larkfield.stop_reason", "") or ""

    @property
    def model_spans(self) -> list[Span]:
        return [s for s in self.spans if s.op == "chat"]

    @property
    def tool_spans(self) -> list[Span]:
        return [s for s in self.spans if s.op == "execute_tool"]

    @property
    def reads(self) -> list[Span]:
        return [s for s in self.spans if s.is_read]

    @property
    def writes(self) -> list[Span]:
        return [s for s in self.spans if s.is_write and s.tool != "send_reply"]

    @property
    def replies(self) -> list[Span]:
        return [s for s in self.spans if s.is_write and s.tool == "send_reply"]

    @property
    def cost(self) -> float:
        return round(sum(s.get("larkfield.cost.usd", 0) or 0 for s in self.model_spans), 8)

    @property
    def tokens(self) -> tuple[int, int]:
        return (sum(s.get("gen_ai.usage.input_tokens", 0) or 0 for s in self.model_spans),
                sum(s.get("gen_ai.usage.output_tokens", 0) or 0 for s in self.model_spans))

    @property
    def duration(self) -> float:
        """Trace 1's length in seconds: the agent's work, without the wait for a person."""
        r = self.root
        return r.seconds if r else 0.0

    @property
    def wait_s(self) -> float | None:
        d = self.decision
        return d.get("larkfield.approval.wait_s") if d else None

    @property
    def approver(self) -> str:
        d = self.decision
        return d.get("larkfield.approval.approver", "") if d else ""


def group_runs(spans: list[Span]) -> dict[str, Run]:
    """Spans -> runs. A span belongs to the run of its trace (the trace's root names the run)."""
    run_of_trace = {}
    for s in spans:
        if not s.parent_id and s.get(RUN_ID):
            run_of_trace.setdefault(s.trace_id, s.get(RUN_ID))
    # a handoff that lost its context starts a trace without a root run ID: keep it by its own run attribute
    for s in spans:
        if s.trace_id not in run_of_trace and s.get(RUN_ID):
            run_of_trace[s.trace_id] = s.get(RUN_ID)
    runs: dict[str, list[Span]] = {}
    for s in spans:
        rid = run_of_trace.get(s.trace_id)
        if rid:
            runs.setdefault(rid, []).append(s)
    out = {}
    for rid, ss in runs.items():
        ss.sort(key=lambda s: (s.start, -s.end))
        out[rid] = Run(rid, ss)
    return dict(sorted(out.items(), key=lambda kv: kv[1].start))


class Telemetry:
    """One folder of saved telemetry, with its runs and their flags."""

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.spans = load_spans(self.folder)
        self.runs = group_runs(self.spans)
        from .flags import flag_run
        for run in self.runs.values():
            run.flags = flag_run(run)

    def events(self) -> list[dict]:
        return load_events(self.folder)

    def find(self, key: str) -> Run | None:
        """A run by its run ID, a trace ID, or a ticket (the last run of that ticket)."""
        if key in self.runs:
            return self.runs[key]
        for run in self.runs.values():
            if key in run.trace_ids:
                return run
        matches = [r for r in self.runs.values() if r.ticket == key]
        if matches:
            return matches[-1]
        matches = [r for rid, r in self.runs.items() if rid.startswith(key)]
        return matches[-1] if matches else None
