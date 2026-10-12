# Capstone: the document assistant (end of Module 1)

The project is chosen and bounded. Sam's worked example: a document support assistant for the help desks of two shops, Larkfield and Bramble Books. No product code yet: Module 1 decides what to build and how to prove it.

## First run

```sh
python3 -m venv .venv && source .venv/bin/activate      # Windows: py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m scripts.holdout check
python -m pytest
```

`holdout check` proves that the held-out questions did not change after they were reserved.

## What Module 1 added

- `docs/project-brief.md`: one user, one decision, the documents, the non-goals, the track and the milestones.
- `docs/acceptance-criteria.md`: testable behaviour, quality thresholds, access rules and the budget.
- `docs/evidence-plan.md`: the evidence for every claim.
- `evaluation/questions.jsonl`: the question bank (103 questions, two shops).
- `evaluation/heldout.jsonl`, `dev.jsonl`, `heldout.lock`: the held-out questions, reserved with `python -m scripts.holdout reserve` before any tuning, and the tuning questions.

## Reset

`git checkout evaluation/` restores the reserved files. Never reserve again after you have seen results.
