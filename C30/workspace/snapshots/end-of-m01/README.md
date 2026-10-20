# Your QA workspace: end-of-m01

This folder is your QA workspace at the stage "end-of-m01" of the course *Testing AI Applications: Manual and
AI-Assisted QA*. It holds your test cases, plans, notes, bug reports and sign-offs. It holds no code: the app and
the QA runner are in the `practice-app` folder next to it.

Use it if you are stuck, or to start a module with the course's version: copy the contents of this folder into
`ai-qa/workspace` (next to `snapshots/`), replacing your files of the same name.

New in this stage: Your first hunt: ten questions sorted into failure types (`notes/first-hunt.md`), and the same check with 1 run and with 10 runs.

## Run the cases

In the `practice-app` folder, with its virtual environment active:

```
python -m qa run ../workspace/cases
```

The last line should be:

```
3 case(s): 2 passed, 1 failed, 0 known bug(s) still failing, 0 known bug(s) now passing, 0 not run
```

FAIL lines are expected: the practice app has bugs on purpose, and these cases find some of them.

## Files

- `cases/one-run-is-not-enough.yaml`
- `cases/smoke.yaml`
- `notes/first-hunt.md`
