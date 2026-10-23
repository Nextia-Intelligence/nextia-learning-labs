# Rolling the platform out at Larkfield: a worked plan

The replayed month (`reference` scenario, `evidence/estate-report-2026-09.md`) followed this plan in fast time.
Real teams need weeks, not days, for each phase.

| Phase | What happens | What we measure |
|---|---|---|
| 0. Inventory | list every AI use: the apps we know, the provider bills, the egress log, a scan of the code | findings outside the registry |
| 1. Registration first | every app fills in the short form; high risk also the long form and a review | registrations; time from request to active |
| 2. New agents through the gateway | every new agent gets its own credentials and calls only the gateway | share of new agents through the gateway |
| 3. Move existing apps one by one | triage, then the document assistant, then the workflow, then the judge; each changes its base URL and credential | provider calls through the gateway (the bill) |
| 4. Close the side doors | revoke the old team keys and personal keys; the egress rule allows only the gateway | calls around the gateway; blocked connections |
| 5. Run it | budgets, kill-switch drills, reviews, the monthly report, exceptions with an end date | friction: refusals per agent and why |

When not to run your own gateway: one team, one provider and one app. The provider's own project keys, budgets
and limits may be enough, or a managed gateway. The gateway pays once several teams share models, providers and
budgets.
