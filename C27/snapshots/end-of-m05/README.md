# Capstone: the document assistant (end of Module 5)

The assistant is measured on the held-out questions, the isolation checks run on three layers, and one change chosen from the tuning questions' errors is in place: keyword search next to the vectors, fused by reciprocal rank fusion (`RETRIEVAL_MODE=hybrid`). The cross-encoder reranker is an option (`dense_rerank`, `hybrid_rerank`): measured, slower, not better here. `docs/evaluation-report.md` compares the baseline and the candidate, with the regressions and the cost: on the held-out questions the candidate is not proven better, only no worse.

## First run

```sh
python3 -m venv .venv && source .venv/bin/activate      # Windows: py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env && python -m idp init
docker compose up -d --wait db                           # --wait: until the database is ready
python -m scripts.load_pack
python -m scripts.isolation                              # must say 0 leaks
python -m scripts.evaluate --set heldout                 # recorded answers: the report's numbers, without a key
python -m pytest
```

## What Module 5 added

- `doc_assistant/evaluate.py`, `scripts/evaluate.py`: the measures and the runner (`--set dev|heldout`, `--config`, `--retrieval-only`).
- `scripts/isolation.py`: search, API and database checks across the two shops.
- The change: `migrations/004_keyword_search.sql`, `retrieve.py` (the four modes and the fusion), `rerank.py` (the reranker option).
- `docs/evaluation-report.md`.

## Reset

`python -m scripts.load_pack --reset`.
