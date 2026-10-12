# Telemetry schema of the ticket service

The service sends three signals with OpenTelemetry (`ticket_api/telemetry.py`). This page lists
what is in them, so that dashboards, alerts and `python -m ops` can rely on the names.

## Where it goes

| Setting | Default | What it does |
|---|---|---|
| `TELEMETRY_FILE` | empty | JSON Lines files; `{service}` becomes `ticket-api` or `ticket-worker` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | empty | an OpenTelemetry Collector, for example `http://127.0.0.1:4318` (Grafana stack) |
| `TELEMETRY_SAMPLE` | 1.0 | the share of tickets that get a trace (logs and metrics: every ticket) |
| `TELEMETRY_CAPTURE_CONTENT` | false | put ticket text, replies and questions into telemetry (do not) |
| `TELEMETRY_REDACT` | true | before export: remove text attributes, mask e-mail addresses and card numbers |
| `TELEMETRY_RETENTION_DAYS` | 30 | how long saved telemetry is kept (`python -m ops prune`) |
| `TELEMETRY_METRIC_INTERVAL_MS` | 15000 | how often metrics are sent |

Resource attributes on everything: `service.name`, `service.version` (1.5.0),
`deployment.environment.name`, `app.release.id`.

## Traces: one per ticket

`POST /v1/tickets` (API, server span) → database spans → the job's span `process ticket job`
(worker, consumer span, in the same trace: the job keeps the request's `traceparent`) →
`triage` → `chat chat-small` (client span, GenAI attributes) → `embed` → `cache get` /
`embeddings embed-small`; database spans for each query. Questions: `POST /v1/answers` →
`chat chat-small`.

GenAI attributes (OpenTelemetry's GenAI semantic conventions, still in development):
`gen_ai.operation.name`, `gen_ai.provider.name`, `gen_ai.request.model`,
`gen_ai.request.max_tokens`, `gen_ai.response.model`, `gen_ai.response.finish_reasons`,
`gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`,
`gen_ai.usage.reasoning_output_tokens`; and the service's own `app.cost_usd`,
`app.evidence` (replayed or simulated), `prompt.version`, `app.release.id`, `app.outcome`.

## Logs: one event per step of a ticket

Every event has `request.id` (the API's request ID, also in the worker's events for that
ticket) and the trace and span IDs.

| Event | Service | Attributes |
|---|---|---|
| `ticket.received` | API | `ticket.id`, `job.id`, `http.status_code`, `ticket.channel`, `ticket.message_chars`, `ticket.language_guess`, `ticket.message_sha256` (16 characters), `customer.ref` (a hash), `release.id` |
| `ticket.triaged` | worker | `ticket.id`, `job.id`, `job.attempt`, `release.id`, `release.canary`, `prompt.version`, `outcome` (ok, no_answer, bad_answer, rejected, dead_letter, failed, sent_to_person), `team`, `needs_human`, `language`, `time_to_draft_s`, `triage_ms`, `cost_usd`, `gen_ai.*` (model, finish reason, tokens), `evidence`, `error.type` |
| `job.retry` | worker | `ticket.id`, `job.state` (retried, waiting, released), `error.type` |
| `ticket.shadowed` | worker | the shadow release's `outcome`, `team`, `needs_human`, tokens, cost |
| `ticket.reviewed` | API | `ticket.id`, `label.team`, `label.needs_human`, `assistant.team`, `assistant.needs_human`, `agrees`, `review.delay_s`, `prompt.version`, `release.id` |
| `answer.served` | API | `cache`, `latency_ms`, `sources` (doc@version), `stale_sources`, `docs.version`, `index.version`, `question.chars` |
| `release.changed` | worker | `release.active`, `release.canary`, `release.canary_share`, `release.shadow` |
| `breaker.changed` | worker | `breaker.state` (open, half_open, closed) |

Never in telemetry by default: the ticket's subject and body, the reply, the question and the
answer, a customer's ID or e-mail address.

## Metrics (names as Prometheus shows them)

| Metric | Labels |
|---|---|
| `app_tickets_received_total` | `http_status_code` |
| `app_tickets_triaged_total` | `outcome`, `prompt_version`, `release_id`, `needs_human` |
| `app_ticket_time_to_draft_seconds` (histogram) | `release_id` |
| `app_ai_cost_USD_total` | `task`, `prompt_version`, `release_id` |
| `gen_ai_client_token_usage` (histogram) | `gen_ai_token_type`, `gen_ai_operation_name`, `gen_ai_request_model`, `gen_ai_response_model`, `app_prompt_version` |
| `gen_ai_client_operation_duration_seconds` (histogram) | `gen_ai_operation_name`, `gen_ai_request_model`, `error_type`, `app_prompt_version` |
| `app_tickets_reviewed_total` | `agrees`, `prompt_version`, `release_id`, `label_needs_human` |
| `app_answers_served_total`, `app_answer_duration_seconds` | `cache`, `stale` |
| `app_queue_depth` (gauge), `app_queue_oldest_age_seconds`, `app_provider_breaker_open_ratio` | `state` |

The outcome and review counters start at 0 for every release and prompt, so that the first
real event shows as an increase.

## The file format (what python -m ops reads)

One JSON object per line: `{"signal": "log" | "span" | "metric", ...}`; times in seconds since
1970 (UTC). See `ops/telemetry.py`.
