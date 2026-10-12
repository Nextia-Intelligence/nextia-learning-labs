# Runbook: a release makes the answers worse

**Alerts:** `no-answer` (SEV-2), `draft-fast-burn` (SEV-2), `cost-over-budget` (SEV-3).
**Owner:** Priya (the prompt and its quality) with Amira (the release). **Customer message:** Grace.

## Detection

- Answers without text: the model used all its tokens and wrote nothing. The ticket has no
  team, no needs-a-person decision, no draft. A safety ticket would reach nobody.
- Dashboard *Ticket service: release comparison*: the canary's share of answers without text,
  its cost per ticket and its time, against the active release.

## Triage (5 minutes)

1. Which release made the bad answers? `python -m ops quality FILE --by release` or the
   release comparison dashboard. If only the canary has them, it is the release.
2. Since when? `python -m ops rollout history`: the last change and who made it.

## Mitigation

- Roll back first, investigate after: `python -m ops rollout rollback --reason "..."`.
  The worker takes it within 5 seconds. Rolling back is safe: the active release passed its gate.
- Find the tickets that got no answer since the release (outcome `no_answer` in the
  `ticket.triaged` events, or `ai_runs` with status `error`) and send them to agents now.
  Safety tickets first.

## Escalation

- Any safety ticket without an answer: SEV-1. Grace calls the customer.
- Tell Omar (the release's owner) and the team that wrote the prompt.

## Recovery checks (the evidence)

- [ ] `python -m ops canary FILE`: after the last release change, no new answer without text
      and no canary ticket.
- [ ] Cost per 1,000 tickets and the triage time are back to the active release's values.
- [ ] Every ticket without an answer has reached a person (list them, with their owners).
- [ ] An experiment record says why the release failed (`operations/experiments/`).
