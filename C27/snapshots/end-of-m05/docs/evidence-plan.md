# Evidence plan: the document assistant

Sam's plan from Module 1. For every claim in the README and the demo, the artifact that proves it. A claim without evidence is not made.

## Claims and evidence

| Claim | Evidence | Made in module |
|---|---|---|
| A new user can upload a document and get a cited answer | the README's quick start, run on a clean computer; a screenshot of the page; `tests/test_api.py` | 3, 6 |
| Answers cite their sources, and the citations are real | citation validity in the evaluation report; `tests/test_answers_unit.py` | 3, 5 |
| A shop never sees another shop's data | `python -m scripts.isolation` (0 leaks); `tests/test_access.py`; row-level security in migration 002 | 4, 5 |
| It says "no answer" instead of guessing | abstention on the held-out unanswerable and other-shop questions | 5 |
| Bad files, repeated uploads and a slow model are handled | `python -m scripts.failure_cases`; `tests/test_failures.py` | 4 |
| Deleting a document removes everything | `tests/test_deletion.py` | 4 |
| One change improved it, with evidence | the evaluation report: baseline against candidate on the held-out questions | 5 |
| It runs from a clean environment | the CI workflow and the smoke test; the Compose demo | 6 |
| It costs under US$0.001 per question | the cost per question in the evaluation report (recorded token counts × the price list) | 5 |

## Held-out questions

- Where they are: `evaluation/heldout.jsonl`, reserved with `python -m scripts.holdout reserve` (seed 27, 40% of each shop's questions of each kind), locked by `evaluation/heldout.lock`.
- How many: 41 (Larkfield 27, Bramble Books 14), of nine kinds: answerable, version, table, exact code, contradiction, staff-only, injection bait, unanswerable and another shop's questions.
- Rule: tune and inspect errors on `evaluation/dev.jsonl` (62 questions) only. Run the held-out questions once per compared version, at the end.

## What I will not claim

- "Production-ready": it ran on one laptop, with synthetic documents and a practice identity provider.
- "Secure": it passed the checks listed here; nobody tested it as an attacker would.
- Anything about real shops, real users or time saved: nobody used it for real work.
