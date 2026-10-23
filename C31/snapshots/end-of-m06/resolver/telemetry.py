"""OpenTelemetry for the workflow: one place that sets up traces, metrics and events, and decides where they go.

    OBS_EXPORT=file        (default) OTLP JSON files in work/telemetry/: traces.jsonl, metrics.jsonl, logs.jsonl.
                           `python -m obs` reads them. Audit events also go straight to the audit store.
    OBS_EXPORT=otlp        OTLP over HTTP to a Collector (OTEL_EXPORTER_OTLP_ENDPOINT, default
                           http://127.0.0.1:4318). The Collector redacts, samples traces and routes audit events.
    OBS_EXPORT=file,otlp   both
    OBS_EXPORT=off         nothing is recorded (the agents course's workflow, as it was)

The application never knows where its data ends up: that is the Collector's job (Module 2). It knows only
what it records, and it records no text: no ticket, prompt, answer or tool result (CONTENT below).

Time. Every span gets its times from a run clock (RunClock): it starts at the wall clock when a run
starts, and it moves forward by the RECORDED latency of each replayed model call (a replay answers in
microseconds, the real call took seconds). So a replayed run's waterfall shows the real model's timing.
The replayed week (scenarios/) starts its run clocks at the week's practice times instead.
"""

import base64
import contextlib
import contextvars
import json
import os
import threading
import time
from pathlib import Path

from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry._logs import SeverityNumber
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs import LogRecordProcessor
from opentelemetry.sdk._logs.export import LogRecordExporter, LogRecordExportResult, SimpleLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (InMemoryMetricReader, MetricExporter, MetricExportResult,
                                              PeriodicExportingMetricReader)
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace import Link, SpanKind, Status, StatusCode

from . import conventions as c
from .data import PROJECT, WORK

SERVICE = "support-workflow"
VERSION = "2.0.0"
CONTENT = os.environ.get("OBS_CAPTURE_CONTENT", "off") == "on"   # off: never put text on telemetry


# ------------------------------------------------------------------ OTLP JSON (the format the Collector's file
# exporter writes and its otlpjsonfile receiver reads: one export request per line, IDs in hex)

def _hex_ids(node):
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if k in ("traceId", "spanId", "parentSpanId") and isinstance(v, str):
                node[k] = base64.b64decode(v).hex() if v else ""
            else:
                _hex_ids(v)
    elif isinstance(node, list):
        for x in node:
            _hex_ids(x)
    return node


def otlp_json(message) -> dict:
    from google.protobuf.json_format import MessageToDict
    return _hex_ids(MessageToDict(message))


class _Lines:
    """One JSON object per line, appended under a lock (several threads may export)."""
    lock = threading.Lock()

    def __init__(self, path: Path):
        self.path = path

    def write(self, obj: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        with self.lock, self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


class FileSpanExporter(SpanExporter):
    def __init__(self, path: Path):
        self.out = _Lines(path)

    def export(self, spans):
        from opentelemetry.exporter.otlp.proto.common.trace_encoder import encode_spans
        self.out.write(otlp_json(encode_spans(spans)))
        return SpanExportResult.SUCCESS

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self):
        pass


class FileLogExporter(LogRecordExporter):
    def __init__(self, path: Path):
        self.out = _Lines(path)

    def export(self, batch):
        from opentelemetry.exporter.otlp.proto.common._log_encoder import encode_logs
        # Audit events go to the audit store only (AuditRouter), as the Collector's routing does.
        batch = [r for r in batch if not (getattr(getattr(r, "log_record", r), "event_name", "") or "")
                 .startswith("larkfield.audit.")]
        if batch:
            self.out.write(otlp_json(encode_logs(batch)))
        return LogRecordExportResult.SUCCESS

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def shutdown(self):
        pass


class FileMetricExporter(MetricExporter):
    def __init__(self, path: Path, **kw):
        super().__init__(**kw)
        self.out = _Lines(path)

    def export(self, metrics_data, timeout_millis: float = 10_000, **kw):
        from opentelemetry.exporter.otlp.proto.common.metrics_encoder import encode_metrics
        self.out.write(otlp_json(encode_metrics(metrics_data)))
        return MetricExportResult.SUCCESS

    def force_flush(self, timeout_millis: float = 10_000) -> bool:
        return True

    def shutdown(self, timeout_millis: float = 30_000, **kw):
        pass


class AuditRouter(LogRecordProcessor):
    """In file mode there is no Collector: this sends every audit event straight to the audit store.

    It never samples and never drops: an audit event that cannot be stored raises, and the run fails
    loudly (a missing audit record is worse than a failed run). With a Collector (OBS_EXPORT=otlp), the
    Collector's audit pipeline does this job instead (collector/*.yaml).
    """

    def __init__(self, store):
        self.store = store

    def on_emit(self, log_record):
        record = getattr(log_record, "log_record", log_record)
        name = getattr(record, "event_name", None) or ""
        if name.startswith("larkfield.audit."):
            self.store.append(json.loads(record.body))

    emit = on_emit

    def shutdown(self):
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True


# ------------------------------------------------------------------ the run clock

class RunClock:
    """A run's own time line in nanoseconds (see the module docstring)."""

    def __init__(self, start_ns: int | None = None):
        self.ns = start_ns if start_ns is not None else time.time_ns()

    def now(self) -> int:
        return self.ns

    def advance(self, seconds: float) -> int:
        self.ns += max(0, int(seconds * 1e9))
        return self.ns


_clock: contextvars.ContextVar[RunClock | None] = contextvars.ContextVar("run_clock", default=None)


def clock() -> RunClock:
    current = _clock.get()
    if current is None:
        current = RunClock()
        _clock.set(current)
    return current


@contextlib.contextmanager
def run_clock(start_ns: int | None = None):
    token = _clock.set(RunClock(start_ns))
    try:
        yield _clock.get()
    finally:
        _clock.reset(token)


# ------------------------------------------------------------------ setup

class Telemetry:
    """The providers and the instruments. `get()` makes one from the environment the first time."""

    def __init__(self, export: str | None = None, folder: Path | None = None, release: str = VERSION,
                 audit_path: Path | None = None, sampler=None, metric_reader=None, id_generator=None,
                 key_seed: str | None = None):
        self.export = {x.strip() for x in (export or os.environ.get("OBS_EXPORT", "file")).split(",") if x.strip()}
        self.folder = Path(folder or os.environ.get("OBS_TELEMETRY", WORK / "telemetry"))
        self.release = os.environ.get("OBS_RELEASE", release)
        self.enabled = "off" not in self.export
        resource = Resource.create({"service.name": SERVICE, "service.version": self.release,
                                    "deployment.environment.name": os.environ.get("OBS_ENVIRONMENT", "practice")})
        kw = {"sampler": sampler} if sampler is not None else {}
        if id_generator is not None:
            kw["id_generator"] = id_generator
        self.tracer_provider = TracerProvider(resource=resource, **kw)
        self.logger_provider = LoggerProvider(resource=resource)
        readers = [metric_reader] if metric_reader is not None else []
        self.audit = None
        if self.enabled:
            from auditstore.store import AuditStore
            if "file" in self.export:
                self.tracer_provider.add_span_processor(SimpleSpanProcessor(FileSpanExporter(self.folder / "traces.jsonl")))
                self.logger_provider.add_log_record_processor(
                    SimpleLogRecordProcessor(FileLogExporter(self.folder / "logs.jsonl")))
                self.audit = AuditStore(Path(audit_path or os.environ.get("OBS_AUDIT", WORK / "audit" / "audit.jsonl")),
                                        key_seed=key_seed)
                self.logger_provider.add_log_record_processor(AuditRouter(self.audit))
                if metric_reader is None:
                    readers.append(PeriodicExportingMetricReader(FileMetricExporter(self.folder / "metrics.jsonl"),
                                                                 export_interval_millis=3_600_000))
            if "otlp" in self.export:
                from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
                from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
                from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
                from opentelemetry.sdk.trace.export import BatchSpanProcessor
                self.tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
                # Audit events are sent at once and in order: a batch could be lost if the process dies.
                self.logger_provider.add_log_record_processor(SimpleLogRecordProcessor(OTLPLogExporter()))
                readers.append(PeriodicExportingMetricReader(   # also with a reader of our own (the replayed week)
                    OTLPMetricExporter(), export_interval_millis=int(os.environ.get("OBS_METRIC_INTERVAL_MS", "10000"))))
        views = [View(instrument_name=c.M_INFERENCE_DURATION, aggregation=ExplicitBucketHistogramAggregation(c.DURATION_BUCKETS)),
                 View(instrument_name=c.M_AGENT_DURATION, aggregation=ExplicitBucketHistogramAggregation(c.DURATION_BUCKETS)),
                 View(instrument_name=c.M_TOOL_DURATION, aggregation=ExplicitBucketHistogramAggregation(c.DURATION_BUCKETS)),
                 View(instrument_name=c.M_APPROVAL_WAIT, aggregation=ExplicitBucketHistogramAggregation(c.WAIT_BUCKETS)),
                 View(instrument_name=c.M_STEPS, aggregation=ExplicitBucketHistogramAggregation([1, 2, 3, 4, 5, 6, 8, 10]))]
        self.meter_provider = MeterProvider(resource=resource, metric_readers=readers, views=views)
        self.tracer = self.tracer_provider.get_tracer("larkfield.support-workflow", VERSION, schema_url=c.SCHEMA_URL)
        self.logger = self.logger_provider.get_logger("larkfield.support-workflow", VERSION)
        m = self.meter_provider.get_meter("larkfield.support-workflow", VERSION, schema_url=c.SCHEMA_URL)
        self.inference_duration = m.create_histogram(c.M_INFERENCE_DURATION, unit="s",
                                                     description="GenAI client inference operation duration")
        self.input_tokens = m.create_counter(c.M_INPUT_TOKENS, unit="{token}", description="Input tokens")
        self.output_tokens = m.create_counter(c.M_OUTPUT_TOKENS, unit="{token}", description="Output tokens")
        self.agent_duration = m.create_histogram(c.M_AGENT_DURATION, unit="s", description="Agent run duration")
        self.tool_duration = m.create_histogram(c.M_TOOL_DURATION, unit="s", description="Tool call duration")
        self.runs = m.create_counter(c.M_RUNS, unit="{run}", description="Finished runs by outcome")
        self.run_cost = m.create_counter(c.M_RUN_COST, unit="{USD}", description="Model cost of runs in US dollars")
        self.tool_calls = m.create_counter(c.M_TOOL_CALLS, unit="{call}", description="Tool calls")
        self.writes = m.create_counter(c.M_WRITES, unit="{write}", description="Write calls by outcome")
        self.approval_wait = m.create_histogram(c.M_APPROVAL_WAIT, unit="s", description="Approval waiting time")
        self.steps = m.create_histogram(c.M_STEPS, unit="{call}", description="Model calls per run")

    def flush(self) -> None:
        self.tracer_provider.force_flush()
        self.logger_provider.force_flush()
        self.meter_provider.force_flush()

    def shutdown(self) -> None:
        self.tracer_provider.shutdown()
        self.logger_provider.shutdown()
        self.meter_provider.shutdown()

    # -------------------------------------------------------------- spans with run-clock times

    @contextlib.contextmanager
    def span(self, name: str, attributes: dict | None = None, kind: SpanKind = SpanKind.INTERNAL,
             links: list[Link] | None = None, parent=None, start_ns: int | None = None):
        """A span that starts and ends on the run clock, and is the current span inside the block."""
        ctx = trace.set_span_in_context(parent) if parent is not None else None
        s = self.tracer.start_span(name, context=ctx, kind=kind, attributes=clean(attributes or {}), links=links,
                                   start_time=start_ns if start_ns is not None else clock().now())
        token = otel_context.attach(trace.set_span_in_context(s))
        try:
            yield s
        except Exception as e:
            s.set_status(Status(StatusCode.ERROR, type(e).__name__))
            s.set_attribute(c.ERROR_TYPE, type(e).__name__)
            raise
        finally:
            otel_context.detach(token)
            s.end(end_time=max(clock().now(), getattr(s, "start_time", 0) or 0))

    # -------------------------------------------------------------- events

    def event(self, name: str, attributes: dict | None = None, body=None, severity=SeverityNumber.INFO) -> None:
        if not self.enabled:
            return
        self.logger.emit(timestamp=clock().now(), observed_timestamp=clock().now(), event_name=name,
                         severity_number=severity, attributes=clean(attributes or {}),
                         body=json.dumps(body, ensure_ascii=False, sort_keys=True) if isinstance(body, dict) else body,
                         context=otel_context.get_current())


def clean(attributes: dict) -> dict:
    """OpenTelemetry attributes: no None values; lists of strings; nothing else than str, bool, int, float."""
    out = {}
    for k, v in attributes.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            out[k] = [str(x) for x in v]
        elif isinstance(v, (str, bool, int, float)):
            out[k] = v
        else:
            out[k] = json.dumps(v, ensure_ascii=False, sort_keys=True)
    return out


_lock = threading.Lock()
_current: Telemetry | None = None


def get() -> Telemetry:
    global _current
    with _lock:
        if _current is None:
            _current = Telemetry()
        return _current


def use(t: Telemetry | None) -> Telemetry | None:
    """Replace the telemetry (the tests and the replayed week use their own). Returns the earlier one."""
    global _current
    with _lock:
        old, _current = _current, t
        return old


def current_traceparent() -> str:
    """The W3C traceparent of the current span ('' when there is none)."""
    ctx = trace.get_current_span().get_span_context()
    if not ctx.is_valid:
        return ""
    return f"00-{ctx.trace_id:032x}-{ctx.span_id:016x}-{int(ctx.trace_flags):02x}"


def span_ref(span) -> dict:
    ctx = span.get_span_context()
    return {"trace_id": f"{ctx.trace_id:032x}", "span_id": f"{ctx.span_id:016x}", "flags": int(ctx.trace_flags)}


def link_to(ref: dict | None, **attributes) -> list[Link]:
    """A span link to a span saved as span_ref() (for example the approval request of the first trace)."""
    if not ref or not ref.get("trace_id"):
        return []
    from opentelemetry.trace import SpanContext, TraceFlags
    sc = SpanContext(int(ref["trace_id"], 16), int(ref["span_id"], 16), is_remote=True,
                     trace_flags=TraceFlags(ref.get("flags", 1)))
    return [Link(sc, clean(attributes))]


_ids = None


def seed_ids(seed: int | None) -> None:
    """Make event IDs reproducible (the replayed week); None: random again."""
    global _ids
    import random
    _ids = random.Random(seed) if seed is not None else None


def new_id() -> str:
    import uuid
    if _ids is None:
        return str(uuid.uuid4())
    return str(uuid.UUID(int=_ids.getrandbits(128), version=4))


class SeededIds:
    """A span and trace ID generator with a seed, so that a replayed week has the same IDs every time."""

    def is_trace_id_random(self) -> bool:
        return True

    def __init__(self, seed: int):
        import random
        self.rng = random.Random(seed)

    def generate_span_id(self) -> int:
        return self.rng.getrandbits(64) or 1

    def generate_trace_id(self) -> int:
        return self.rng.getrandbits(128) or 1


def prompt_version(name: str) -> str:
    """The version of a prompt file: the first 8 characters of its SHA-256 (policy included)."""
    import hashlib
    folder = PROJECT / "resolver" / "prompts"
    text = (folder / f"{name}.md").read_bytes() + (folder / "policy.md").read_bytes()
    return hashlib.sha256(text).hexdigest()[:8]
