# Runbooks of the ticket service

A runbook says what to do when an alert fires: how you know (detection), what you check
first (triage), what you do to protect customers (mitigation), whom you call (escalation),
and how you prove that the service is back (recovery checks). Every alert in
`observability/alerts/` and `operations/alerts.toml` names its runbook.

| Runbook | Alerts | Owner |
|---|---|---|
| [provider-outage.md](provider-outage.md) | provider-circuit-open, drafts-late, triage-slow | Kwame (provider), Amira (service) |
| [bad-release.md](bad-release.md) | no-answer, draft-fast-burn, cost-over-budget | Priya (prompt), Amira (release) |
| [stale-index.md](stale-index.md) | old-sources | Tomás |
| [model-version-changed.md](model-version-changed.md) | model-version-changed | Priya |
| [quality-drop.md](quality-drop.md) | reviews-disagree | Priya |
| [tickets-refused.md](tickets-refused.md) | accept-fast-burn | Amira |

Severity levels and response times are in `operations/slos.toml`. Grace speaks to customers;
the person on call never writes to customers alone.

After every SEV-1 or SEV-2 incident, write a post-incident review within 5 working days
(`operations/reviews/`): what happened, why, and the actions that stop it from happening
again, each with an owner.
