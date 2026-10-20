# Your QA workspace: end-of-m05

This folder is your QA workspace at the stage "end-of-m05" of the course *Testing AI Applications: Manual and
AI-Assisted QA*. It holds your test cases, plans, notes, bug reports and sign-offs. It holds no code: the app and
the QA runner are in the `practice-app` folder next to it.

Use it if you are stuck, or to start a module with the course's version: copy the contents of this folder into
`ai-qa/workspace` (next to `snapshots/`), replacing your files of the same name.

New in this stage: An agent-ready bug report with its failing case, a GitHub issue form, and the review of a recorded coding agent's fix.

## Run the cases

In the `practice-app` folder, with its virtual environment active:

```
python -m qa run ../workspace/cases
```

The last line should be:

```
24 case(s): 8 passed, 11 failed, 5 known bug(s) still failing, 0 known bug(s) now passing, 0 not run
```

FAIL lines are expected: the practice app has bugs on purpose, and these cases find some of them.

## Files

- `.github/ISSUE_TEMPLATE/ai-bug.yml`
- `bugs/BUG-001-invented-refund-amount.md`
- `bugs/BUG-002-outdated-returns-policy.md`
- `bugs/BUG-003-other-customers-order.md`
- `bugs/BUG-004-empty-message-error.md`
- `bugs/BUG-005-agent-ready.md`
- `bugs/BUG-005-weed-killer-refused.md`
- `bugs/evidence/bug-001-seed4.json`
- `bugs/evidence/bug-002-seed2.json`
- `bugs/evidence/bug-003-seed1.json`
- `bugs/evidence/bug-004-seed1.json`
- `bugs/evidence/bug-005-seed5.json`
- `cases/bugs.yaml`
- `cases/failing/bug-005-weed-killer.yaml`
- `cases/hostile-inputs.yaml`
- `cases/metamorphic-refunds.yaml`
- `cases/metamorphic.yaml`
- `cases/one-run-is-not-enough.yaml`
- `cases/properties.yaml`
- `cases/repro-rate.yaml`
- `cases/smoke.yaml`
- `notes/charter-01-refunds.md`
- `notes/first-hunt.md`
- `notes/fix-review-bug-005.md`
- `notes/session-01-refunds.md`
- `notes/triage.md`
- `plan/acceptance-criteria.md`
- `plan/metamorphic-relations.md`
- `plan/refund-risks.md`
- `plan/risk-table.md`
- `plan/rubric-refund-reply.md`
