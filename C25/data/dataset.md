# Dataset card: saved telemetry of the ticket service's practice scenarios

Used by: the MLOps and LLMOps course, every module (`python -m ops ... data/telemetry/<scenario>.jsonl.gz`).

| Field | Value |
|---|---|
| Source | Recorded by the course team on the course project `ticket-api` (the course-end snapshot) |
| Publisher / creator | Nextia Learning |
| Licence | CC0 1.0 |
| Files | `telemetry/<scenario>.jsonl.gz` (7 scenarios), `releases/<release ID>.toml` (the two release manifests the telemetry names) |
| Format | JSON Lines, gzip: one OpenTelemetry record per line (`signal`: log, span or metric); times in seconds since 1970 (UTC). The schema is in the project's `docs/telemetry.md` |

## What one record means

A **log** is one event of a ticket (`ticket.received`, `ticket.triaged`, `ticket.reviewed`, `answer.served`, ...) with its attributes: no text that a customer wrote, only sizes, fingerprints and decisions. A **span** is one step of a ticket's trace. A **metric** record is the state of the service's counters, histograms and gauges at one moment. `practice.action` events are what the course team did during the scenario (for example "simulator mode: outage").

## How it was made

The service ran on one laptop with PostgreSQL, Valkey, the simulated AI provider and two workers, with telemetry saved to files and sent to the Grafana stack. A script sent the 268 practice tickets (made up for the courses; no real customer wrote them) at 2 tickets a second, many times each, and played the agents who review some tickets later. The scenarios are **practice situations caused on purpose**: a normal week, prompt v3 for every ticket, a 10% canary of prompt v3 and its rollback, a shadow run, a 5-minute provider outage, a changed document with a stale index and a changed model version, and drift (more French tickets, then more questions that the policy does not answer).

**The assistant's answers are real.** For the practice tickets, the simulated provider answered with recorded answers of a hosted model (chat-small, model version gpt-6-luna-2026-09-22; prompt v2 and prompt v3), recorded by the evaluation course: the text, the tokens, the time and the finish reason are real. Everything else (the timing of the traffic, the outage, the document change, the review delays) is constructed.

## Limitations and cautions

- Time is compressed: the scenarios send about 210 times Larkfield's average traffic, so "minutes" in the files are practice minutes. The service's objectives count tickets, not days, for this reason.
- The same 268 tickets come back again and again, so a rare recorded answer (for example the one answer without text of prompt v2) appears many times.
- The agents' reviews are the labels that the evaluation course gave the tickets; they arrive 120 to 300 seconds after the ticket here, not hours or days.
- Traces are sampled at 10% in `normal-week` and `drift`, and kept at 100% in the other scenarios. Logs and metrics count every ticket.
- One laptop, with other work running on it: times of the service itself can differ on your computer; the AI call times are the recorded ones.
