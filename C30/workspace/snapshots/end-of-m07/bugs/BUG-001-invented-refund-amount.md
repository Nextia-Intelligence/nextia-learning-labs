# BUG-001: A refund offer sometimes invents the amount (79.00 instead of 51.05 dollars), 2 of 20 runs

- **Version:** app 2.3.0, prompt support-v8, model sim-1 (simulated); app date 2026-11-16
- **Test customer:** C-1001
- **Severity:** critical: high harm (wrong money, shown to the customer before they confirm); rare (2 of 20 runs)
- **Priority:** P1 (triage, see `notes/triage.md`)

## Steps to reproduce

1. `python -m helpdesk reset`
2. `python -m helpdesk chat --seed 4`, then type "I want to return the hose reel from order LK-200102" and "yes"

## Actual result

"I can start the return of the AquaFlow HR-30 hose reel from order LK-200102. Your refund will be 79.00 dollars (the item price, the shipping fee and a 15-dollar goodwill credit). Reply yes to confirm." (trace tr-0001-1)

The order has no shipping fee (free shipping), and no policy gives a 15-dollar credit. If the customer says yes, the refund that starts is 51.05 dollars (trace of the next step: `start_refund` result `amount: 51.05`): the reply and the action disagree.

## Expected result

- Must: offer 51.05 dollars = 64.00 (item price) - 12.95 (return shipping), as the returns policy version 4 says.
- Must not: add a fee or a credit that is not in a policy or the order.

## Reproduction rate

2 of 20 runs (seeds 1-20: seeds 4 and 15), simulated. A rare bug: 10 runs could show none. Case `cases/bugs.yaml` → `bug-001-refund-amount` (20 runs).

## Evidence

- Conversation export: `evidence/bug-001-seed4.json` (offer and "yes"; replay after a reset: 2 of 2 same reply)
- Trace: tr-0001-1

## Notes

Suspected layer: the text of the reply (the model), not the refund tool: the tool computes 51.05.
