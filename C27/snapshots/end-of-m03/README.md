# Capstone: the document assistant (end of Module 3)

One complete user journey works: upload a document, watch it get indexed, ask a question and get an answer with citations. Nobody signs in yet: every request acts as Sam, a practice user (Module 4 adds sign-in and access control).

## First run

```sh
python3 -m venv .venv && source .venv/bin/activate      # Windows: py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
# Linux without a GPU: pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp .env.example .env                                     # then change the password
docker compose up -d --wait db                           # --wait: until the database is ready
python -m scripts.load_pack                              # migrations, the two shops and their 51 documents (downloads the models once)
python -m scripts.ask "How long is a gift card valid?" --tenant bramble
fastapi dev doc_assistant/main.py                        # the page: http://127.0.0.1:8000
python -m pytest
```

Answers come from `ANSWER_PROVIDER` in `.env`: `recorded` (the default: real answers of chat-small, recorded by the course team; the mock answers any other question, and says so), `mock` (no model), or `live` (your own OpenAI-compatible endpoint and key).

## What Module 3 added

- The API (`doc_assistant/main.py`, `documents.py`, `answers.py`, `errors.py`, `models.py`): validated endpoints, one error shape, uploads as jobs with states.
- Ingestion (`ingest.py`, `worker.py`, `chunk.py`, `embed.py`): parse, chunk and embed in a background thread.
- The answer pipeline (`retrieve.py`, `context.py`, `answer.py`, `cite.py`, `providers.py`, `pipeline.py`, `tracing.py`): dense search in PostgreSQL, the answer with citations, checked in code, traced.
- The page (`doc_assistant/static/`): one plain HTML page with `fetch`, no build step.
- `scripts/load_pack.py`, `ask.py`, `trace.py`.

## Reset

`python -m scripts.load_pack --reset`.
