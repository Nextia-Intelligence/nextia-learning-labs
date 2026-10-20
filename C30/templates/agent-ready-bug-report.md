# <ID>: <summary: what goes wrong, where, how often>

<!-- A report that a coding agent (or a developer) can act on without asking you questions. An agent cannot
guess what you did not write: give exact inputs, checkable expected behaviour, how to prove the fix, and what it
must not change. Keep secrets and personal data out. -->

## Summary

<one or two sentences: the behaviour, its impact, and how often it happens>

## Environment

- App build: <version, commit or folder>
- Model: <name and version; simulated or real>
- Prompt / config version: <...>
- Flags and settings: <seed, app date, live mode or not>
- Role / test account: <C-1001 (test)>

## Steps

1. <exact command or input, word for word>
2. Attached conversation: `<file>.json` (export with versions, seed and traces)

## Actual

- Output: <the reply, word for word, or the part that matters>
- Trace ID: <tr-...>
- Tool calls / retrieved documents: <from the trace>

## Expected (checkable)

- Must: <rule, for example "ask for confirmation and call no tool in the first reply">
- Must not: <rule, for example "call cancel_order before the customer says yes">

## Reproduction rate

<x> of <y> runs, seeds <...>, <settings>

## Suspected layer

<retrieval / prompt / model / tool or permission code / app code> - a guess, because <reason from the trace>

## Acceptance criteria

- [ ] The attached failing case passes <N>/<N> runs: `python -m qa run <case file> --runs <N>`
- [ ] The existing suite passes: `python -m qa run <regression folder>`
- [ ] No change to the safety rules, the confirmation rules or the permission checks

## Constraints for the fixer

- Touch only: <files or parts, if you know them>
- Do not: change or delete tests or cases, hard-code answers for the test input, weaken or remove a rule, add a new dependency

## Attached failing case

```yaml
<paste the case from failing-case.yaml>
```
