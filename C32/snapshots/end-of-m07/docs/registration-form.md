# The registration form

Every agent and app fills in the **short form** before its first call (`registrations/<id>.yaml`). A high-risk
registration also fills in the **long form**. `python -m estate check FILE` lists what is missing.

| Field | Short form | What the platform does with it |
|---|---|---|
| `id`, `name`, `kind` | yes | the agent's identity (its client ID) |
| `owner`, `team` | yes | who answers for it; an owner who left the company blocks the registration |
| `purpose`, `users` | yes | the inventory; the governance report |
| `risk_tier` | yes | the review interval (high 3 months, medium 6, low 12) and the failure mode |
| `data_classes` | yes | the gateway refuses a request with another data class; payment data never goes to a model |
| `capabilities` | yes | the gateway refuses any other capability |
| `tools` | yes | the tool gateway refuses any other tool |
| `autonomy` | yes | `suggests`, `acts-with-approval` or `acts`; a high-risk agent may not `act` |
| `budget_usd_month`, `limits` | yes | hard stops at the gateway (budget, tokens a day, requests a minute, model calls per run) |
| `review_date` | yes | `python -m estate review-due` lists overdue reviews |
| `evaluations` | when it uses a capability | the remap gate runs this evaluation before a capability changes model |
| `pins` | when it needs one model | the gateway keeps that exact model until `retire_by` |
| `long_form.impact`, `human_oversight`, `failure_mode`, `incident_contact`, `data_retention`, `kill_switch_tested` | high risk only | the review, the failure mode, the incident contact |
