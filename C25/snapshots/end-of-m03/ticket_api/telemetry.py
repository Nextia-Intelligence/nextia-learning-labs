"""Telemetry with OpenTelemetry: traces, metrics and logs (the MLOps course, Module 3).

The API and the worker send three signals:
- traces: one trace per ticket, from POST /v1/tickets through the job, the triage and embed
  calls, the cache and the database. Each step is a span with a start, an end and attributes;
- metrics: numbers added up over time (tickets, outcomes, tokens, cost, time to a draft, the
  queue);
- logs: one event per step of a ticket (ticket.received, ticket.triaged, ...), each with the
  request ID and the trace ID, so a log line leads to its trace.

Where they go (both, one, or none):
- TELEMETRY_FILE: JSON Lines files on your computer, "{service}" becomes ticket-api or
  ticket-worker. python -m ops reads them; no other program is needed.
- OTEL_EXPORTER_OTLP_ENDPOINT: an OpenTelemetry Collector (http://127.0.0.1:4318 for the
  course's Grafana stack: docker compose --profile observability up -d).
With neither, the code runs the same, and the telemetry goes nowhere.

Privacy (Lesson 3): by default no ticket text, no reply and no question is put in telemetry
(TELEMETRY_CAPTURE_CONTENT=false). Before export, redaction (TELEMETRY_REDACT=true) removes
the attributes that hold text and masks e-mail addresses and card numbers in what is left.
Traces are sampled (TELEMETRY_SAMPLE: the share of tickets that get a trace); metrics and
logs are not, so the SLIs count every ticket.
"""

import json
import logging
import re
import threading
import time
from contextvars import ContextVar
from pathlib import Path

from opentelemetry import trace
from opentelemetry._logs import LogRecord, SeverityNumber
from opentelemetry.sdk._logs.export import LogRecordExporter, LogRecordExportResult
from opentelemetry.sdk.metrics.export import MetricExporter, MetricExportResult
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import SpanKind, StatusCode

SERVICE_VERSION = "1.5.0"
# The request that a log line belongs to: the API sets it for each request, the worker for
# each job (the ID of the request that created the ticket).
REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
# The prompt version of the current job: AI call metrics carry it, so dashboards can compare
# prompt versions.
PROMPT_VERSION: ContextVar[str | None] = ContextVar("prompt_version", default=None)

# Attributes that hold text that people wrote: never exported when redaction is on.
CONTENT_KEYS = frozenset(
    {
        "ticket.subject",
        "ticket.body",
        "gen_ai.input.messages",
        "gen_ai.output.messages",
        "gen_ai.system_instructions",
        "question.text",
        "answer.text",
    }
)
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")

_state: dict = {"on": False, "redact": True, "capture": False}
_lock = threading.Lock()
logger = logging.getLogger("ticket_api.telemetry")


# ---------- redaction (Lesson 3) ----------


def mask(text: str) -> str:
    """E-mail addresses and card numbers in a text, replaced by [email] and [card]."""
    return _CARD.sub("[card]", _EMAIL.sub("[email]", text))


def redact(attributes: dict | None) -> dict:
    """The attributes without the text that people wrote, and with e-mail addresses and card
    numbers masked in the rest."""
    out = {}
    for key, value in (attributes or {}).items():
        if key in CONTENT_KEYS:
            continue
        if isinstance(value, str):
            value = mask(value)
        elif isinstance(value, (list, tuple)):
            value = [mask(v) if isinstance(v, str) else v for v in value]
        out[key] = value
    return out


def capture_content() -> bool:
    """True only when TELEMETRY_CAPTURE_CONTENT=true: the text may be added to telemetry."""
    return _state["capture"]


# ---------- the file exporters (JSON Lines that python -m ops reads) ----------


class JsonlFile:
    """Appends records to one file, one JSON object per line, one write per batch."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def write(self, records: list[dict]) -> None:
        if not records:
            return
        text = "".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in records)
        with self.lock, self.path.open("a", encoding="utf-8") as f:
            f.write(text)


def _plain(value):
    if isinstance(value, tuple):
        return [_plain(v) for v in value]
    return value


def _attrs(attributes) -> dict:
    return {k: _plain(v) for k, v in (attributes or {}).items()}


def make_exporters(out: JsonlFile | None, otlp: str | None):
    """The exporters: to the file (python -m ops reads it) and to the collector (OTLP)."""

    class RedactingSpanExporter(SpanExporter):
        """Removes text and masks e-mail addresses in every span before the next exporter."""

        def __init__(self, inner):
            self.inner = inner

        def export(self, spans):
            if not _state["redact"]:
                return self.inner.export(spans)
            clean = [
                ReadableSpan(
                    name=s.name,
                    context=s.context,
                    parent=s.parent,
                    resource=s.resource,
                    attributes=redact(dict(s.attributes or {})),
                    events=s.events,
                    links=s.links,
                    kind=s.kind,
                    status=s.status,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    instrumentation_scope=s.instrumentation_scope,
                )
                for s in spans
            ]
            return self.inner.export(clean)

        def shutdown(self):
            self.inner.shutdown()

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            return self.inner.force_flush(timeout_millis)

    class FileSpanExporter(SpanExporter):
        def export(self, spans):
            out.write(
                [
                    {
                        "signal": "span",
                        "name": s.name,
                        "service": s.resource.attributes.get("service.name"),
                        "trace_id": format(s.context.trace_id, "032x"),
                        "span_id": format(s.context.span_id, "016x"),
                        "parent_id": format(s.parent.span_id, "016x") if s.parent else None,
                        "kind": s.kind.name.lower(),
                        "start": s.start_time / 1e9,
                        "end": s.end_time / 1e9,
                        "status": "error" if s.status.status_code == StatusCode.ERROR else "ok",
                        "error": s.status.description,
                        "attributes": _attrs(s.attributes),
                    }
                    for s in spans
                ]
            )
            return SpanExportResult.SUCCESS

        def shutdown(self):
            pass

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            return True

    class FileLogExporter(LogRecordExporter):
        def export(self, batch):
            rows = []
            for item in batch:
                r = item.log_record
                attrs = _attrs(r.attributes)
                rows.append(
                    {
                        "signal": "log",
                        "time": (r.timestamp or r.observed_timestamp or time.time_ns()) / 1e9,
                        "service": item.resource.attributes.get("service.name"),
                        "severity": r.severity_text,
                        "event": r.event_name or attrs.pop("event.name", None),
                        "body": r.body,
                        "trace_id": format(r.trace_id, "032x") if r.trace_id else None,
                        "span_id": format(r.span_id, "016x") if r.span_id else None,
                        "attributes": attrs,
                    }
                )
            out.write(rows)
            return LogRecordExportResult.SUCCESS

        def shutdown(self):
            pass

        def force_flush(self, timeout_millis: int = 30000) -> bool:
            return True

    class FileMetricExporter(MetricExporter):
        def __init__(self):
            super().__init__()

        def export(self, metrics_data, timeout_millis: float = 10_000, **kwargs):
            rows = []
            for rm in metrics_data.resource_metrics:
                service = rm.resource.attributes.get("service.name")
                for sm in rm.scope_metrics:
                    for m in sm.metrics:
                        points = []
                        for p in m.data.data_points:
                            point = {"attributes": _attrs(p.attributes)}
                            if hasattr(p, "bucket_counts"):
                                point |= {
                                    "count": p.count,
                                    "sum": p.sum,
                                    "bounds": list(p.explicit_bounds),
                                    "buckets": list(p.bucket_counts),
                                }
                            else:
                                point["value"] = p.value
                            points.append(point)
                        rows.append(
                            {
                                "signal": "metric",
                                "time": time.time(),
                                "service": service,
                                "name": m.name,
                                "unit": m.unit,
                                "kind": type(m.data).__name__.lower(),
                                "points": points,
                            }
                        )
            out.write(rows)
            return MetricExportResult.SUCCESS

        def force_flush(self, timeout_millis: float = 10_000) -> bool:
            return True

        def shutdown(self, timeout_millis: float = 30_000, **kwargs) -> None:
            pass

    spans, logs, metrics = [], [], []
    if out is not None:
        spans.append(RedactingSpanExporter(FileSpanExporter()))
        logs.append(FileLogExporter())
        metrics.append(FileMetricExporter())
    if otlp:
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        base = otlp.rstrip("/")
        spans.append(RedactingSpanExporter(OTLPSpanExporter(endpoint=f"{base}/v1/traces")))
        logs.append(OTLPLogExporter(endpoint=f"{base}/v1/logs"))
        metrics.append(OTLPMetricExporter(endpoint=f"{base}/v1/metrics"))
    return spans, logs, metrics


# ---------- start and stop ----------


def enabled(settings) -> bool:
    return bool(settings.telemetry_file or settings.otlp_endpoint)


def start(settings, service: str) -> bool:
    """Start telemetry for this process (once). Returns True if it is on."""
    with _lock:
        if _state["on"] or not enabled(settings):
            return _state["on"]
        from opentelemetry import _logs, metrics
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

        _state.update(
            on=True, redact=settings.telemetry_redact, capture=settings.telemetry_capture_content
        )
        resource = Resource.create(
            {
                "service.name": service,
                "service.version": SERVICE_VERSION,
                "deployment.environment.name": settings.deployment_environment,
                "app.release.id": settings.release_id or "none",
            }
        )
        out = None
        if settings.telemetry_file:
            out = JsonlFile(settings.telemetry_file.replace("{service}", service))
        span_x, log_x, metric_x = make_exporters(out, settings.otlp_endpoint)

        tracer_provider = TracerProvider(
            resource=resource, sampler=ParentBased(TraceIdRatioBased(settings.telemetry_sample))
        )
        for x in span_x:
            tracer_provider.add_span_processor(BatchSpanProcessor(x, schedule_delay_millis=2000))
        trace.set_tracer_provider(tracer_provider)

        readers = [
            PeriodicExportingMetricReader(x, export_interval_millis=settings.metric_interval_ms)
            for x in metric_x
        ]
        meter_provider = MeterProvider(resource=resource, metric_readers=readers)
        metrics.set_meter_provider(meter_provider)

        logger_provider = LoggerProvider(resource=resource)
        for x in log_x:
            logger_provider.add_log_record_processor(
                BatchLogRecordProcessor(x, schedule_delay_millis=2000)
            )
        _logs.set_logger_provider(logger_provider)
        # The service's own log lines (logging) stay on the console, with the request ID; the
        # exported logs are the events below, which have fixed names and attributes.

        _instrument_libraries(tracer_provider, meter_provider)
        _state.update(tracer=tracer_provider, meter=meter_provider, logs=logger_provider)
        return True


def _instrument_libraries(tracer_provider, meter_provider) -> None:
    """Spans for the database and the HTTP client, made by the libraries' instrumentations."""
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

    PsycopgInstrumentor().instrument(tracer_provider=tracer_provider, skip_dep_check=True)
    HTTPXClientInstrumentor().instrument(
        tracer_provider=tracer_provider, meter_provider=meter_provider
    )


def instrument_app(app) -> None:
    """Server spans for every request of the API (one per request)."""
    if not _state["on"]:
        return
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=_state["tracer"],
        meter_provider=_state["meter"],
        excluded_urls="health,ready",
        exclude_spans=["receive", "send"],
    )


def quiet():
    """No spans for what is inside (the worker's polling of the queue: not a ticket's work)."""
    from opentelemetry.instrumentation.utils import suppress_instrumentation

    return suppress_instrumentation()


def flush() -> None:
    """Send everything that waits in the batches now (the tests, and before a process stops)."""
    if not _state["on"]:
        return
    _state["tracer"].force_flush()
    _state["logs"].force_flush()
    _state["meter"].force_flush()


def shutdown() -> None:
    if _state["on"]:
        flush()
        _state["tracer"].shutdown()
        _state["logs"].shutdown()
        _state["meter"].shutdown()


# ---------- what the service's code calls ----------

tracer = trace.get_tracer("ticket_api", SERVICE_VERSION)


def meter():
    from opentelemetry import metrics

    return metrics.get_meter("ticket_api", SERVICE_VERSION)


class RequestIdFilter(logging.Filter):
    """Adds the request ID to every log record, and masks e-mail addresses in the message."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID.get() or "-"
        if _state["redact"] and isinstance(record.msg, str):
            record.msg = mask(record.msg)
        return True


def event(name: str, attributes: dict, body: str = "", severity: str = "INFO") -> None:
    """One log record for one event of a ticket, with the request ID and the current trace."""
    if not _state["on"]:
        return
    from opentelemetry import _logs

    attrs = {"request.id": REQUEST_ID.get(), **attributes}
    attrs = {k: v for k, v in attrs.items() if v is not None}
    if _state["redact"]:
        attrs, body = redact(attrs), mask(body)
    number = {"INFO": SeverityNumber.INFO, "WARN": SeverityNumber.WARN}.get(
        severity, SeverityNumber.ERROR
    )
    _logs.get_logger("ticket_api.events", SERVICE_VERSION).emit(
        LogRecord(
            timestamp=time.time_ns(),
            body=body or name,
            attributes=attrs,
            event_name=name,
            severity_text=severity,
            severity_number=number,
        )
    )


def span(name: str, kind: SpanKind = SpanKind.INTERNAL, attributes: dict | None = None):
    """A span around a step (use it with `with`)."""
    return tracer.start_as_current_span(name, kind=kind, attributes=attributes)


def trace_ids() -> tuple[str | None, str | None]:
    """The current trace and span IDs (hex), or None."""
    ctx = trace.get_current_span().get_span_context()
    if not ctx.is_valid:
        return None, None
    return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")


def traceparent() -> str | None:
    """The W3C traceparent of the current span: saved with a job, so the worker's spans join
    the same trace as the request that created the ticket."""
    from opentelemetry.propagate import inject

    carrier: dict = {}
    inject(carrier)
    return carrier.get("traceparent")


def context_from(traceparent_value: str | None):
    from opentelemetry.propagate import extract

    return extract({"traceparent": traceparent_value}) if traceparent_value else None


# ---------- the inputs, described without their text ----------

_FRENCH = (
    " je ",
    " j'",
    " mon ",
    " ma ",
    " mes ",
    " est ",
    " pas ",
    " une ",
    " le ",
    " la ",
    " les ",
    "bonjour",
    "merci",
    " vous ",
    " pour ",
    " avec ",
)


def language_guess(text: str) -> str:
    """ "fr" or "en", from common short words: a cheap description of the input (for drift),
    not the assistant's answer."""
    low = f" {text.lower()} "
    return "fr" if sum(w in low for w in _FRENCH) >= 3 else "en"


def fingerprint(text: str) -> str:
    """16 characters of the SHA-256 of a text: the same text gives the same fingerprint, and
    the text cannot be read back from it."""
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def customer_ref(customer_id: str) -> str:
    """A customer's reference in telemetry: a hash, not the ID."""
    return fingerprint(f"customer:{customer_id}")[:10]


# ---------- the metrics (counted for every ticket, never sampled) ----------


class Instruments:
    """Created once; they do nothing until telemetry starts (the API's proxy meter)."""

    def __init__(self) -> None:
        m = meter()
        self.received = m.create_counter(
            "app.tickets.received", "{ticket}", "Ticket requests, by HTTP status"
        )
        self.triaged = m.create_counter(
            "app.tickets.triaged", "{ticket}", "Finished ticket jobs, by outcome and release"
        )
        self.time_to_draft = m.create_histogram(
            "app.ticket.time_to_draft",
            "s",
            "From the ticket's arrival to its triage result",
            explicit_bucket_boundaries_advisory=[
                1,
                2,
                5,
                10,
                20,
                30,
                60,
                120,
                300,
                600,
                1800,
                3600,
            ],
        )
        self.tokens = m.create_histogram(
            "gen_ai.client.token.usage",
            "{token}",
            "Tokens per AI call (GenAI semantic conventions)",
            explicit_bucket_boundaries_advisory=[1, 16, 64, 256, 1024, 2048, 4096, 16384],
        )
        self.duration = m.create_histogram(
            "gen_ai.client.operation.duration",
            "s",
            "Time of each AI call (GenAI semantic conventions)",
            explicit_bucket_boundaries_advisory=[0.1, 0.25, 0.5, 1, 2, 3, 5, 8, 12, 20, 30],
        )
        self.cost = m.create_counter("app.ai.cost", "USD", "Estimated AI cost (dated prices)")
        self.answers = m.create_counter("app.answers.served", "{answer}", "Answers to questions")
        self.answer_time = m.create_histogram(
            "app.answer.duration",
            "s",
            "Time to answer a question",
            explicit_bucket_boundaries_advisory=[0.05, 0.1, 0.25, 0.5, 1, 2, 3, 5, 10],
        )
        self.reviewed = m.create_counter(
            "app.tickets.reviewed", "{ticket}", "Agents' reviews of the assistant's decisions"
        )


# Every combination of these labels starts at 0, so that the first real event shows up as an
# increase (Prometheus cannot see an increase in a series that starts at 1).
OUTCOME_LABELS = (
    ("ok", "true"),
    ("ok", "false"),
    ("no_answer", "none"),
    ("bad_answer", "none"),
    ("rejected", "none"),
    ("dead_letter", "none"),
    ("failed", "none"),
    ("sent_to_person", "true"),
)
_zeroed: set = set()


def zero_series(prompt: str, release: str) -> None:
    """Start the outcome, cost and review counters of a prompt and release at 0 (once)."""
    if (prompt, release) in _zeroed or not _state["on"]:
        return
    _zeroed.add((prompt, release))
    m = instruments()
    for outcome, needs in OUTCOME_LABELS:
        m.triaged.add(
            0,
            {
                "outcome": outcome,
                "prompt.version": prompt,
                "release.id": release,
                "needs_human": needs,
            },
        )
    for agrees in ("true", "false"):
        for needs in ("true", "false"):
            m.reviewed.add(
                0,
                {
                    "agrees": agrees,
                    "prompt.version": prompt,
                    "release.id": release,
                    "label.needs_human": needs,
                },
            )


def zero_api_series() -> None:
    if not _state["on"] or "api" in _zeroed:
        return
    _zeroed.add("api")
    m = instruments()
    for code in (202, 404, 422, 429, 500, 502, 503):
        m.received.add(0, {"http.status_code": code})
    for cache in ("hit", "miss", "wait", "off"):
        for stale in ("true", "false"):
            m.answers.add(0, {"cache": cache, "stale": stale})


_instruments: Instruments | None = None


def instruments() -> Instruments:
    global _instruments
    if _instruments is None:
        _instruments = Instruments()
    return _instruments
