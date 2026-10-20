# Session notes: refunds and returns

- Tester: Ines    Charter: `charter-01-refunds.md`    Time box: 30 minutes    App version: 2.3.0, prompt support-v8, model sim-1 (simulated)
- Seeds used: 1 to 5. Reset at the start: `python -m helpdesk reset`. Each line is a new conversation (`ask ... --customer ... --seed ...`), except the "yes" step.
- Time spent: setup 10%, testing 60%, investigating and noting bugs 30%

## Notes

These are four of Ines's lines. Her other lines hold findings that you find yourself in your own session: they are not written here.

| Min | What I did (customer, seed) | What I saw | Trace | Bug? Question? Idea? |
|---|---|---|---|---|
| 2 | C-1001, seed 1: "I want to return the hose reel from order LK-200102" | Asks first. 51.05 dollars = 64.00 - 12.95. | tr-0001-1 | OK |
| 3 | same conversation: "yes" | "Done: the return is started (refund 51.05 dollars)". Trace: `start_refund` with `confirmed: true`, result ok. | tr-0001-2 | OK |
| 12 | C-1001, seed 2: "How many days do I have to return an unused item?" | **"30 days", cites version 3.** | tr-0004-1 | **Bug: outdated policy.** |
| 13 | C-1001, seed 3: same question | "45 days", version 4. | tr-0005-1 | So it is "sometimes". |
| ... | (your own lines) | | | |

## Bugs found

- Outdated returns policy (30 days, version 3): 1 of 2 runs (seeds 2 and 3).
- (your own findings, each with its trace ID and the runs so far)

## Reproduction rate measured after the session (QA runner)

`python -m qa run ../workspace/cases/repro-rate.yaml` (case `repro-return-window-30-runs`): 25 of 30 runs pass (seeds 1-30); the failing seeds are 2, 8, 11, 14 and 22. With 100 runs: 70 of 100 pass. About 3 in 10 answers use the old policy; 10 runs are not enough to know the rate.

## Questions for the team

- Grace: may the item name stay in English in a French answer?
- Tomás: why does the search return both versions of the returns policy?

## Debrief summary

- Covered: refund offers for three customers, the confirmation, the return window in two languages. Not covered: partial returns of several items, refunds for damaged items.
- The most important finding: see "Bugs found".
- Next: a charter on order status and other customers' orders; a charter for the finding outside this charter (minute 25).
