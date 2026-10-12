# Capstone: the document assistant (end of Module 2)

The data and the design are ready, before any integration is built: a two-shop data pack, the architecture and contracts, the core database schema, and the threat and cost review.

## First run

```sh
python3 -m venv .venv && source .venv/bin/activate      # Windows: py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                                     # Windows: copy .env.example .env; then change the password
docker compose up -d --wait db                           # PostgreSQL 18 with pgvector; --wait: until it is ready
python -m scripts.datapack                               # checksums, every document parses, the difficulties
python -m doc_assistant.migrate                          # applies migrations/001_core.sql
python -m pytest
```

## What Module 2 added

- `data/`: Larkfield's 36 documents and Bramble Books' 15, their inventories, the people and memberships, `SHA256SUMS` and the data card `data/dataset.md`.
- `doc_assistant/parse.py`: one parser for Markdown, HTML and PDF (the RAG course's).
- `docs/design-pack/architecture.md`: components, the API contract, the data model, ingestion states, retrieval metadata.
- `migrations/001_core.sql`, `doc_assistant/migrate.py`, `doc_assistant/config.py`, `compose.yaml`: the schema and how to apply it.
- `docs/design-pack/threat-and-cost.md`: trust boundaries, threats with their tests, isolation rules and the budget.

## Reset

`docker compose down --volumes` deletes the database; `docker compose up -d --wait db` and `python -m doc_assistant.migrate` make it again.
