# PIR-001: safety tickets waited for nobody after the prompt v3 change

A post-incident review: what happened, why, and what stops it from happening again. It blames
no person. The numbers come from the practice replay of the incident
(`release-full.jsonl.gz` in the course's saved telemetry: a practice incident that we caused
on purpose, with the evaluation course's real recorded answers). The replay sends tickets
about 210 times faster than Larkfield's real traffic: 1,798 tickets with prompt v3 is about
two days of Larkfield's tickets (822 a day).

| | |
|---|---|
| Severity | SEV-1 (tickets that needed a person reached nobody) |
| Owner of this review | Priya |
| People | Amira (service), Priya (prompt), Grace (customers), Omar (the change), Kwame (cost) |
| Status | actions open (below) |

## Summary

To make each ticket cheaper, the live prompt was switched from v2 to v3 for every ticket,
without a canary, after an evaluation that had said DO NOT SHIP (EXP-001). Prompt v3 makes the
model reason until its 1,000-token limit on some tickets and write nothing. Those tickets got
no team, no needs-a-person decision and no draft, and the job failed quietly. The API kept
accepting every ticket, so the service looked up.

## What the telemetry shows (practice replay)

- Accept SLI: **100.00%** (2,400 of 2,400 requests): the "uptime" view stayed green.
- Draft SLI: **91.79%** (2,203 of 2,400), against an objective of 99%: burn rate **8.2**.
- With prompt v3: **186 of 1,798** tickets got an answer without text (10.3%) and **10** became
  dead letters (one recorded answer took 12.1 s, longer than the 10-second timeout, on every
  attempt).
- **10 tickets that needed a person reached nobody**, for 4 different tickets of the practice
  set: T-65663 (a hot, cracked pan; 5 times), T-64740 (a parasol fell toward a child; 3 times),
  T-81044 and T-81036 (once each).
- Cost: US$0.474 per 1,000 tickets with v3, US$0.338 with v2 (+40%). Triage call p95: 8.34 s
  against 5.17 s.
- Agents' reviews: 83.7% agreement with v3 (623 of 744), 93.8% with v2 (288 of 307).

## Timeline (minutes of the replay)

| When | What |
|---|---|
| +0.0 | Prompt v2 active (release 1.5.0-4fafd1). |
| +3.2 | Alert `no-answer` fires: prompt v2 has one recorded answer without text (practice ticket T-65450), and it was sent again. Nobody acts: it looks like noise. |
| +5.0 | Prompt v3 becomes active for every ticket (release 1.5.0-767b56). No canary, no gate. |
| +7.9 | First safety ticket without an answer (T-65663). |
| +9.7 | `triage-slow` fires (rules on saved telemetry; Grafana: +9.95). |
| +10.7 | `draft-fast-burn` fires: SEV-2 (Grafana: +10.6). |
| +10.8 | `reviews-disagree` fires. |
| +11.2 | `cost-over-budget` fires (Grafana: +13.8). |
| +20.1 | End of the replay. Nobody rolled back: in the real incident, these alerts did not exist yet. |

## Causes and contributing conditions

1. **The cause:** prompt v3 asks for a complete, specific answer, and the model then reasons until
   the token limit on some tickets (25 of 271 in the evaluation; 10.3% here).
2. A prompt change was made as a settings change, not a release: no manifest, no gate, no canary.
3. A job without a valid answer failed quietly: the ticket stayed in the default team, with no
   person told (no fallback).
4. The dashboard showed only the accept journey ("uptime"); nothing measured the draft journey.
5. The `no-answer` alert had fired before the change for one ticket of prompt v2, so a new alert
   looked like the same noise.

## Actions (each with an owner)

| Action | Owner | Done in |
|---|---|---|
| A ticket without a valid answer goes to a person (`TRIAGE_FALLBACK=person`) | Amira | Module 6 |
| Every prompt change is a release with a manifest, and passes the gate (`ops gate`) | Priya | Modules 2 and 5 |
| Every release starts as a 10% canary with rollback rules (`operations/rollout.toml`) | Omar | Module 5 |
| SLOs for the draft and safety journeys, and their alerts, on the main dashboard | Amira, Grace | Modules 1 and 3 |
| The `no-answer` alert links the ticket, and prompt v2's known case (T-65450) is reviewed so the alert is trusted | Priya | Module 6 |
| The provider timeout covers the slowest recorded answer, or a long answer is not retried 5 times | Kwame | open |

## How we know it is fixed

Replay the same change as a canary (`canary.jsonl.gz`): the `no-answer` alert fired 1.0 minute
after the canary started; the rollback happened after 25 canary tickets; after the rollback no
canary ticket was sent and the cost and time were back to prompt v2's.
