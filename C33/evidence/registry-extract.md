# Registry extract

> **Constructed** for this course, in the shape of the platform registry that a course on governing AI agents builds. The names, tiers, budgets and review dates are made up. The registry lists only what is registered with the platform.

| Agent ID | System | Owner | Team | Purpose | Risk tier (as registered) | Data classes | Capabilities | Tools | Autonomy | Budget a month | Review | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `triage-service` | S1 | Amira | Service team | Sort tickets and draft replies | low | customer-personal | fast-small | — | acts alone (routing) | US$50 | due in 4 months | active |
| `resolution-workflow` | S2 | Amira | Service team | Propose resolutions; a person approves | medium | customer-personal, payment-status | fast-small | get_ticket, search_knowledge, propose_refund | proposes; a person approves | US$30 | due in 1 month | active |
| `doc-assistant` | S3 | Mei | Data team | Answer staff questions from documents | low | internal, staff-only | fast-small, embed | — | answers a person | US$20 | overdue by 2 months | active |
| `support-mcp` | S4 | Kwame | Platform team | Tools for support applications | medium | customer-personal | — | get_ticket, search_knowledge, propose_refund | proposes; an owner approves | US$0 | due in 5 months | active |

## What the registry cannot tell you

- AI features inside bought tools: they do not call the platform.
- AI that goes around the platform with its own key, like the weekly digest script.
- Whether the tier that a team registered is the right one: the registry stores what it is told.
