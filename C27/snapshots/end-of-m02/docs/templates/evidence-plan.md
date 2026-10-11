# Evidence plan: <your product's name>

Write this in Module 1 (*Plan the evidence*). For every claim you will make in your demo and README, name the artifact that proves it. A claim without evidence is not made.

## Claims and evidence

| Claim | Evidence (a file, a test, a run, a screenshot) | Made in module |
|---|---|---|
| <the assistant cites its sources> | <tests/..., the evaluation report's citation validity> | <3, 5> |

## Held-out questions

- Where they are: `evaluation/heldout.jsonl` (reserved with `python -m scripts.holdout reserve`, locked by `evaluation/heldout.lock`)
- How many, and of which kinds: <...>
- Rule: I tune and inspect errors on `evaluation/dev.jsonl` only. I run the held-out questions once per compared version, at the end.

## What I will not claim

- <for example "production-ready", "secure", "better than ChatGPT": claims that my evidence cannot support>
