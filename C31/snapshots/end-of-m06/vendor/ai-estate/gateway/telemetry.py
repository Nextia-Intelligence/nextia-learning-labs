"""Optional OpenTelemetry spans for the gateway (off by default: GATEWAY_OTEL=on to turn them on).

One span per model call, named "chat <capability>" or "embeddings <capability>", with the attribute names of
OpenTelemetry's GenAI semantic conventions (status "development": they may still change; this project uses the
names of opentelemetry-semantic-conventions 0.66b1) plus the estate's own: larkfield.agent.id, larkfield.team,
larkfield.gateway.check and larkfield.gateway.outcome. No prompt or answer text is put on a span.

The spans use the API package (opentelemetry-api, which the mcp package already installs). To export them,
install requirements-otel.txt and set the usual OTEL_EXPORTER_OTLP_ENDPOINT (for example the observability
course's collector); without an SDK the spans are no-ops.
"""

import os

ENABLED = os.environ.get("GATEWAY_OTEL", "off") == "on"
_tracer = None


def tracer():
    global _tracer
    if _tracer is None:
        from opentelemetry import trace

        _tracer = trace.get_tracer("larkfield.model-gateway", "1.0.0")
    return _tracer


def start(endpoint: str):
    if not ENABLED:
        return None
    return tracer().start_span(f"{endpoint} pending", attributes={"gen_ai.operation.name": endpoint})


def attributes(row: dict) -> dict:
    a = {
        "gen_ai.operation.name": "embeddings" if row.get("capability") == "embed" else "chat",
        "gen_ai.request.model": row.get("capability") or "",
        "gen_ai.response.model": row.get("model_version") or "",
        "gen_ai.provider.name": row.get("provider") or "",
        "gen_ai.usage.input_tokens": int(row.get("tokens_in") or 0),
        "gen_ai.usage.output_tokens": int(row.get("tokens_out") or 0),
        "larkfield.agent.id": row.get("agent_id") or "",
        "larkfield.team": row.get("team") or "",
        "larkfield.gateway.outcome": row.get("outcome") or "",
        "larkfield.gateway.check": row.get("check_name") or "",
        "larkfield.gateway.replica": row.get("replica") or "",
    }
    return {k: v for k, v in a.items() if v not in ("", None)}


def end(span, row: dict) -> None:
    if span is None:
        return
    span.update_name(f"{attributes(row).get('gen_ai.operation.name', 'chat')} {row.get('capability') or ''}".strip())
    for k, v in attributes(row).items():
        span.set_attribute(k, v)
    span.end()
