# BUG-002: The return window answer sometimes uses the expired returns policy (30 days, version 3), 4 of 20 runs

From backlog report BL-104 ("Return days wrong?").

- **Version:** app 2.3.0, prompt support-v8, model sim-1 (simulated); app date 2026-11-16
- **Test customer:** C-1001
- **Severity:** high: medium harm (a customer may give up a valid return or miss 15 days of return rights); sometimes (4 of 20 runs)
- **Priority:** P1 (triage, see `notes/triage.md`)

## Steps to reproduce

1. `python -m helpdesk reset`
2. `python -m helpdesk ask "How many days do I have to return an unused item?" --seed 2`

## Actual result

"Thanks for asking. You can return an unused item within 30 days of delivery for a full refund of the item price. [1] I hope this helps." Source [1]: Returns policy, version 3: Return window. (trace tr-0001-1)

The trace lists two retrieved sections with the same score, 7.926: returns policy version 4 (in force from 2026-11-01) and version 3 (effective to 2026-10-31). `cited` is `returns-policy@3#return-window`. No tool was called.

## Expected result

- Must: say "45 days" and cite the returns policy, version 4.
- Must not: say "30 days" or cite version 3 for a question asked on or after 1 November 2026.

## Reproduction rate

4 of 20 runs (seeds 2, 8, 11, 14), simulated (practice app); 30 of 100 with seeds 1-100. Case `cases/bugs.yaml` → `bug-002-return-window-version`. The same happens in French with seed 2.

## Evidence

- Conversation export: `evidence/bug-002-seed2.json` (replay after a reset: 1 of 1 same reply)
- Trace: tr-0001-1

## Notes

Suspected layer (a guess): retrieval. The search returns the expired version 3 with the same score as version 4, so the reply can use either. Workaround for support agents: quote the returns policy, version 4.
