# Capstone: the document assistant (end of Module 5)

The assistant is measured on the held-out questions, the isolation checks run on three layers, and one improvement chosen from the tuning questions' errors is in place: keyword search next to the vectors, fused, then reread by a cross-encoder (`RETRIEVAL_MODE=hybrid_rerank`). `docs/evaluation-report.md` compares the baseline and the candidate, with the regressions and the cost.

## First run

```sh
python3 -m venv .venv && source .venv/bin/activate      # Windows: py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env && python -m idp init
docker compose up -d db
python -m scripts.load_pack
python -m scripts.isolation                              # must say 0 leaks
python -m scripts.evaluate --set heldout                 # recorded answers: the report's numbers, without a key
python -m pytest
```

## What Module 5 added

- `doc_assistant/evaluate.py`, `scripts/evaluate.py`: the measures and the runner (`--set dev|heldout`, `--config`, `--retrieval-only`).
- `scripts/isolation.py`: search, API and database checks across the two shops.
- The improvement: `migrations/004_keyword_search.sql`, `retrieve.py` (fusion), `rerank.py`.
- `docs/evaluation-report.md`.

## Reset

`python -m scripts.load_pack --reset`.
