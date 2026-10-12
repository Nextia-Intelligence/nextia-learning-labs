"""Traces with OpenTelemetry (the operations course's tool): one trace per question, one span per step.

    ask                        the whole question
      retrieve                 search in PostgreSQL (and the reranker, from Module 5)
      generate                 the model call (provider, model, attempts, tokens)
      check                    the citation checks
      store                    the answer saved with its evidence

The spans go to a file, one JSON object per line (TRACE_FILE, default traces/spans.jsonl), so
that you can read them without any other service: python -m scripts.trace last. To send them to
a collector instead, add an OTLP exporter here (the operations course shows how).
The spans never contain the question's text or the answer: only IDs, sizes and times.
"""

import json
import threading
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

_lock = threading.Lock()
_ready = False


class JsonLinesExporter(SpanExporter):
    def __init__(self, path: str):
        p = Path(path)
        self.path = p if p.is_absolute() else Path(__file__).resolve().parent.parent / p   # the project folder

    def export(self, spans) -> SpanExportResult:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _lock, self.path.open("a", encoding="utf-8") as f:
            for s in spans:
                f.write(json.dumps({
                    "trace_id": format(s.context.trace_id, "032x"), "span_id": format(s.context.span_id, "016x"),
                    "parent_id": format(s.parent.span_id, "016x") if s.parent else None, "name": s.name,
                    "start_ns": s.start_time, "end_ns": s.end_time,
                    "duration_ms": round((s.end_time - s.start_time) / 1e6, 1),
                    "status": s.status.status_code.name, "attributes": dict(s.attributes or {}),
                }) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass


def setup(trace_file: str, version: str) -> None:
    """Once per process. An empty TRACE_FILE turns the file off (the spans are still made)."""
    global _ready
    if _ready:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": "doc-assistant", "service.version": version}))
    if trace_file:
        provider.add_span_processor(SimpleSpanProcessor(JsonLinesExporter(trace_file)))
    trace.set_tracer_provider(provider)
    _ready = True


def tracer():
    return trace.get_tracer("doc_assistant")


def current_trace_id() -> str:
    ctx = trace.get_current_span().get_span_context()
    return format(ctx.trace_id, "032x") if ctx.is_valid else ""
