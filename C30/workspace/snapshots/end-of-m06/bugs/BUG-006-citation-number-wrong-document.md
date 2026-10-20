# BUG-006: A citation number points to the wrong document, 4 of 10 runs

- **Version:** app 2.3.0, prompt support-v8, model sim-1 (simulated)
- **Test customer:** C-1001
- **Severity:** medium: the customer opens a source that does not say what the sentence says (harm 2: trust, wrong reading); 4 of 10 runs for this question
- **Layer (with evidence):** the answer's source list, not the search: the trace's `cited` list has the right order; only the numbering in the reply's list is different.

## Steps to reproduce

1. `python3 -m helpdesk reset`
2. `python3 -m helpdesk ask "Who pays return shipping if the item arrived damaged?" --seed 2`

## Actual result

The reply marks the returns-policy sentence "Return shipping is free when the item arrived damaged..." as [1], but the list says "[1] Damaged, faulty on arrival or wrong items, version 2" and "[2] Returns policy, version 3". Trace `cited`: `returns-policy@3#return-shipping-costs`, then `damaged-or-wrong-items@2#report-within-14-days`.

## Expected result

- Must: the source with number [n] in the list is the document of the sentence marked [n].
- Must not: number the sources in another order than in the reply.

## Reproduction rate

4 of 10 runs (seeds 1-10; case `ret-citation-numbers-match`), simulated.

## Notes

Also cites version 3 (see BUG-002). The list looks sorted by document name.
