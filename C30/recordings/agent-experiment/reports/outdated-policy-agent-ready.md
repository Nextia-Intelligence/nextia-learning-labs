# BUG-008: The return window answer sometimes uses the old returns policy (30 days), 2 of 10 runs

## Summary

Asked about the return window, the assistant sometimes answers "30 days" and cites the returns policy version 3, which ended on 31 October 2026. Version 4 (45 days) is in force on the app date. 2 of 10 runs (seeds 1-10: seeds 2 and 8 fail).

## Environment

- App build: larkfield-helpdesk 2.3.0 (this repository)
- Model: sim-1 (simulated)
- Prompt / config version: support-v8
- Flags and settings: seeds 1-10, app date 2026-11-16
- Role / test account: C-1001 (test)

## Steps

1. `python -m helpdesk reset`
2. `python -m helpdesk ask "How many days do I have to return an unused item?" --seed 2`
3. Attached conversation: `evidence/bug-008-seed2.json`

## Actual

- Output: "Thanks for asking. You can return an unused item within 30 days of delivery for a full refund of the item price. [1] I hope this helps." Sources: "[1] Returns policy, version 3: Return window".
- Trace ID: tr-0001-1 (seed 2).
- Trace: `retrieved` lists returns-policy version 4 AND version 3 (effective_to 2026-10-31) with the same score; the answer used version 3.

## Expected (checkable)

- Must: say 45 days and cite `returns-policy@4`.
- Must not: say 30 days or cite `returns-policy@3` (expired on the app date).
- Must still: keep version 3 in the policy files (orders delivered before 1 November 2026 follow it).

## Reproduction rate

2 of 10 runs (seeds 2 and 8), 4 of 20 runs (seeds 1-20), 109 of 300 runs (seeds 1-300). The rate is about 1 in 3; 10 runs are not enough to see it reliably.

## Suspected layer

Retrieval (a guess): the search returns the expired version 3 next to version 4, so the answer can use either. A policy version should be used only when the app date is between `effective_from` and `effective_to`.

## Acceptance criteria

- [ ] `python -m qa run cases/bug-008.yaml --runs 20`: passes 20/20.
- [ ] `python -m pytest -q` passes.
- [ ] Version 3 stays in `helpdesk/data/policies/`.

## Constraints for the fixer

- Touch only: the policy search (`helpdesk/corpus.py`).
- Do not: delete or edit policy documents, change or delete tests or cases, hard-code "45 days".

## Attached failing case

`cases/bug-008.yaml`
