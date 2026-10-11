# Runbook: the AI provider fails

**Alerts:** `provider-circuit-open` (SEV-2), `drafts-late` (SEV-2), `triage-slow` (SEV-3).
**Owner:** Kwame (the provider contract) with Amira (the service). **Customer message:** Grace.

## Detection

- The circuit breaker is open: the provider failed 5 calls in a row (5xx or timeout).
- The oldest queued ticket waits more than 2 minutes.
- Dashboard *Ticket service: overview*: "Provider circuit" shows OPEN; the queue grows.

## Triage (5 minutes)

1. Is it the provider or us? `curl http://127.0.0.1:8300/admin/stats` (practice) or the
   provider's status page. Look at the error types in "Provider calls per minute, by error".
2. Are tickets lost? No: the API still accepts tickets (202); they wait in the queue. Check
   `GET /v1/queue` and the "Tickets accepted" SLI.
3. How long until the draft SLO breaks? A ticket must get its draft within 10 minutes.

## Mitigation

- Do nothing to the workers: the breaker stops the calls, jobs go back to the queue without
  losing an attempt, and they continue when the provider answers again.
- Tell customers: `GET /v1/status` shows the delayed message on the website automatically
  ("Your ticket is saved, and nothing is lost. Our replies take longer than usual ...").
- Safety tickets do not wait for the assistant: agents read the queue for words such as
  *fire*, *smoke*, *burn*, *child* (Grace's team, by hand) while the provider is down.
- Do not raise retries or timeouts during an outage: that sends more calls to a provider
  that cannot answer.

## Escalation

- After 15 minutes: Kwame opens a ticket with the provider and asks for a time to recovery.
- After 30 minutes: Grace puts a message on the help page and the support phone line.

## Recovery checks (the evidence)

- [ ] The breaker is closed: `python -m ops incident FILE` shows "circuit closed".
- [ ] The queue drains: `GET /v1/queue` shows `oldest_queued_seconds` under 120.
- [ ] Drafts are valid again: the draft SLI is back above 99% in the last 5 minutes.
- [ ] No dead letters were created, or each one is retried: `POST /v1/jobs/{id}/retry`.
- [ ] `GET /v1/status` says "ok".
