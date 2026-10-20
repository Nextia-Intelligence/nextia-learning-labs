# Your QA workspace: end-of-m03

This folder is your QA workspace at the stage "end-of-m03" of the course *Testing AI Applications: Manual and
AI-Assisted QA*. It holds your test cases, plans, notes, bug reports and sign-offs. It holds no code: the app and
the QA runner are in the `practice-app` folder next to it.

Use it if you are stuck, or to start a module with the course's version: copy the contents of this folder into
`ai-qa/workspace` (next to `snapshots/`), replacing your files of the same name.

New in this stage: A test charter and the notes of one exploratory session (`notes/`), cases for hostile inputs and for measuring a reproduction rate.

## Run the cases

In the `practice-app` folder, with its virtual environment active:

```
python -m qa run ../workspace/cases
```

The last line should be:

```
16 case(s): 7 passed, 9 failed, 0 known bug(s) still failing, 0 known bug(s) now passing, 0 not run
```

FAIL lines are expected: the practice app has bugs on purpose, and these cases find some of them.

## Files

- `cases/hostile-inputs.yaml`
- `cases/metamorphic-refunds.yaml`
- `cases/metamorphic.yaml`
- `cases/one-run-is-not-enough.yaml`
- `cases/properties.yaml`
- `cases/repro-rate.yaml`
- `cases/smoke.yaml`
- `notes/charter-01-refunds.md`
- `notes/first-hunt.md`
- `notes/session-01-refunds.md`
- `plan/acceptance-criteria.md`
- `plan/metamorphic-relations.md`
- `plan/refund-risks.md`
- `plan/risk-table.md`
- `plan/rubric-refund-reply.md`
