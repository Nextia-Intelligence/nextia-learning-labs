# Document assistant

Answers from each shop's own documents, with a citation for every claim, or a clear "the documents do not answer this". Two shops share one assistant, Larkfield (home and garden) and Bramble Books (a bookshop), and a shop never sees the other shop's documents. This is the worked capstone of the course *Portfolio Capstone: Build, Evaluate and Ship an AI Product*.

Everything runs on your computer. You need no account and no money: the AI answers are recorded (a real model, chat-small, answered the course's questions once; the assistant replays those answers), and the search runs two small open models on your CPU.

## What it does

- A member of a shop signs in, uploads a policy document (.md, .txt, .html or .pdf) and watches it move from *uploaded* to *indexed*, or to *failed* with a reason.
- They ask a question. The assistant searches only their shop's documents (only the ones their role may read, and only the versions in force on the question's date), writes a short answer from the passages, and cites them. Clicking a citation shows the passage.
- If the documents do not answer, it says so. If the model is slow or down, the user sees a clear error.
- Deleting a document removes its file, its passages and vectors, and the stored answers that cite it.

## Quick start

You need Python 3.12 or newer, Git, and Docker (Docker Desktop on macOS and Windows). About 5 GB of free disk for the models and the image.

macOS and Linux:

```sh
python3 -m venv .venv && source .venv/bin/activate
# Linux without a GPU: install the CPU build of torch first
#   pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cp .env.example .env                    # then change POSTGRES_PASSWORD (and the two URLs) in .env
python -m idp init                      # the practice identity provider's keys; writes two secrets to .env
docker compose up -d db                 # PostgreSQL with pgvector
python -m scripts.load_pack             # the two shops, their people and their 51 documents (downloads the models once)
```

Windows (PowerShell): the same, with `py -3.12 -m venv .venv`, `.venv\Scripts\Activate.ps1` and `copy .env.example .env`.

Then, in two terminals (venv active):

```sh
python -m idp                           # terminal 1: the practice identity provider on http://localhost:8400
fastapi dev doc_assistant/main.py       # terminal 2: the API and the page on http://127.0.0.1:8000
```

Open http://127.0.0.1:8000, choose **Sign in**, and pick a person: **Sam** (staff at Larkfield), **Ines** (owner of Bramble Books), **Omar** (read-only at Larkfield), **Camille** (staff at Larkfield, read-only at Bramble Books) or **Tomás** (a member of nothing). The provider asks for no password: it is for practice only.

Check it from the terminal: `python -m pytest` (the tests), `python -m scripts.ask "How long is a gift card valid?" --tenant bramble`, `python -m scripts.isolation` (must say 0 leaks).

**Reset:** `python -m scripts.load_pack --reset` (deletes every shop's data and loads the pack again), or `docker compose down --volumes` and start again.

**The whole demo in containers** (Module 6): `docker compose --profile app up -d --build --wait`, then `docker compose --profile app run --rm api python -m scripts.load_pack`, then `python scripts/smoke.py http://127.0.0.1:8000`. Stop with `docker compose --profile app down` (`--volumes` also deletes the data).

## Architecture

One API process (FastAPI) serves the page, checks every caller, runs the answer pipeline and runs the ingestion worker in a background thread. PostgreSQL with pgvector keeps everything: documents and their files, chunks and their vectors, answers, and usage. Row-level security is a second lock behind the `tenant_id` in every query. The practice identity provider signs the tokens (RS256); the API reads the shop and the role from its own memberships, never from the token.

```
browser (one plain page) --cookie--> API: identify -> membership -> route
                                       |-- answer pipeline: retrieve (vectors + keywords, reranked) -> assemble
                                       |                    -> model (recorded | live) -> check citations -> store
                                       |-- ingestion worker: parse -> chunk -> embed -> save (one transaction)
                                       '-- PostgreSQL + pgvector (row-level security per shop)
```

The design pack has the details: `docs/design-pack/architecture.md` (components, API contract, data model, ingestion states, retrieval metadata) and `docs/design-pack/threat-and-cost.md` (trust boundaries, threats with their tests, isolation rules, budget).

| Setting (.env) | Default | What it does |
|---|---|---|
| `ANSWER_PROVIDER` | `recorded` | `recorded` (the course team's answers; mock for other questions), `mock` (no model), `live` (`LLM_BASE_URL` + `LLM_API_KEY`, any OpenAI-compatible endpoint) |
| `RETRIEVAL_MODE` | `hybrid_rerank` | `dense` (vectors only) or `hybrid_rerank` (vectors + keywords, fused, reread by a cross-encoder) |
| `PROMPT_VERSION` | `answer_v2` | the answer prompt in `doc_assistant/prompts/` |
| `ASSISTANT_TODAY` | `2026-10-11` | the course's "today" (empty = the real date): policies change with the date |
| `DAILY_QUESTION_LIMIT`, `MONTHLY_BUDGET_USD` | 200, 5 | usage limits per shop (0 = no limit) |
| `PROVIDER_TIMEOUT_S`, `PROVIDER_RETRIES` | 20, 2 | for a live model: timeout of one call, extra attempts after a timeout, 429 or 5xx |

## Data provenance

Every document, shop and person is made up for the course: see `data/dataset.md` (CC0). Larkfield's 36 documents are the RAG course's policy collection; Bramble Books' 15 were written for this course with the same difficulties (two versions of a policy, a contradiction, a table-only answer, staff-only procedures, an instruction hidden in a supplier's document). The 103 questions in `evaluation/` were written by people, not by a model; 41 of them were reserved as the held-out set before any tuning (`evaluation/heldout.lock`).

The two local models: `intfloat/multilingual-e5-small` (MIT) for the vectors and `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (Apache-2.0) for reranking, both pinned to one revision. The recorded answers in `recordings/` were made with chat-small (Azure OpenAI).

## Evaluation

See `docs/evaluation-report.md`: the held-out results, the isolation and failure checks, the error categories and the one improvement, with its regressions and costs. Run it again: `python -m scripts.evaluate --set heldout` (recorded answers: the same numbers without a key).

## Limitations

- Tested on one laptop (macOS, Apple silicon). The Windows and Linux commands are written, not tested by the course team.
- The documents are synthetic, short and clean; real document stores are bigger and messier, and retrieval gets harder.
- The recorded answers cover the course's questions. Any other question gets the mock's answer (labelled) unless you configure a live model.
- The practice identity provider asks for no password. The session cookie lasts up to 8 hours and cannot be revoked earlier; removing a membership takes effect at once.
- The cloud deployment steps in `docs/deployment.md` were written but not run by the course team.
- The keys of the question set are strict regular expressions written by one person: read the failures before you trust a number.

## Licence

MIT (see `LICENSE`). The data pack is CC0.
