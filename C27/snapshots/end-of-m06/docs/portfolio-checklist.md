# Portfolio checklist: the document assistant

Sam's checklist (Module 7). Every claim in the README, the demo and Sam's CV links to evidence that a reviewer can open or run. "Live" = runs on the reviewer's computer; "recorded" = a real run kept in the repository.

## Claims and their evidence

| Claim | Evidence | Live or recorded? |
|---|---|---|
| A new user can upload a document and get a cited answer | README "Quick start"; `scripts/smoke.py`; `tests/test_api.py` | live |
| Answers come only from the shop's own documents | `python -m scripts.isolation`: 430 probes, 0 leaks; `tests/test_access.py` | live |
| A read-only member never gets a staff-only passage | the isolation checks; `tests/test_access.py`; 10 of 11 abstentions in the evaluation report | live; recorded answers |
| It says when the documents do not answer | the evaluation report (5 of 6 refusals; the one failure is named) | recorded |
| Citations are checked in code | `doc_assistant/cite.py`; citation validity 100% on the held-out set | live; recorded |
| Bad files, a slow model and deletion are handled | `python -m scripts.failure_cases`; `tests/test_failures.py`, `tests/test_deletion.py` | live |
| The held-out questions were reserved before tuning | `evaluation/heldout.lock` and the commit that added it, before any result | in the repository |
| One change was tested with evidence | `docs/evaluation-report.md`, baseline and candidate, two passes each | recorded |
| It costs about US$0.00017 per question | the evaluation report (token counts × the price list) | recorded |
| It runs from a clean environment | `.github/workflows/ci.yml`; the Compose demo; `docs/runbook.md` (the rollback drill) | live |

## Completed and planned

- Completed: one journey for two shops; sign-in and roles; row-level security; failure handling; deletion; evaluation with a held-out set; a local, reproducible demo with CI, limits and a tested rollback.
- Planned (not done): a cloud deployment (steps written in `docs/deployment.md`, not run); French tuning questions; a fix for questions that name another shop; the extensions in `docs/reflection.md`.
