# Snapshots: ticket-api at the start and at the end of each module

Each folder here is the `ticket-api` project of [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/). `start` is the project that you download in the first lesson: the end of [Scaling APIs and AI Workloads](https://learning.nextia-ai.com/courses/scaling/), unchanged. The others are the project after the last lesson of one module. If your project is broken or missing, copy the snapshot of the module that you finished last, and continue with the next lesson.

| Snapshot | Use it to start | What it has (new) | Tests |
|---|---|---|---|
| [`start`](start) | Module 1 | The scaling course's project: queue, worker, cache, simulated provider. | 176 |
| [`end-of-m01`](end-of-m01) | Module 2 | The assistant as the triage step (`ticket_api/assistant.py`, migration 015), real recorded answers in the simulator, practice tickets (`scripts/practice.py`), the `ops` tool (`summary`, `inventory`, `slo`), `operations/inventory.toml`, `slos.toml`, the service brief. | 185 |
| [`end-of-m02`](end-of-m02) | Module 3 | Release manifests (`ticket_api/releases.py`, migration 016, `RELEASE_ID`), `ops release`, `ops trace`, `ops experiments`, experiment record EXP-001. | 193 |
| [`end-of-m03`](end-of-m03) | Module 4 | Telemetry with OpenTelemetry (`ticket_api/telemetry.py`, migration 017), the Grafana stack (`observability/`, Compose profile `observability`), `ops waterfall`, `quality`, `privacy`, `prune`. | 200 |
| [`end-of-m04`](end-of-m04) | Module 5 | Agents' reviews (migration 018, `scripts/send_reviews.py`), the answers' retrieval index (migration 019, `scripts/reindex.py`, `update_document.py`), `ops drift`, `labels`, `rag`. | 207 |
| [`end-of-m05`](end-of-m05) | Module 6 | The release gate (`ops gate`), canary and shadow releases (migration 020, `ops rollout`, `ops canary`), practice scenarios (`scripts/scenario.py`), `docs/improve.md`. | 213 |
| [`end-of-m06`](end-of-m06) | The final assignment | The fallback to a person, `GET /v1/status`, runbooks, `ops alerts`, `ops incident`, the post-incident review, the course's two release manifests. The course-end project. | 218 |

Each snapshot has only what the lessons' guided practice makes. It does not have the answers to the "Your turn" tasks.

## What a snapshot does not have

- `.env` and `secrets/`. Make them from `.env.example`, as the snapshot's `README.md` says.
- The virtual environment `.venv`, your `telemetry/` files and `practice/` files.
- Your database and your cache: they live in Docker. `python -m scripts.load --reset` loads the data again.

## Use a snapshot

The steps use `end-of-m03` as an example. Use the name of your snapshot.

1. Get the files. If you have Git, clone this repository once, in `~/projects`: `git clone https://github.com/usmanahmed99/nextia-learning-labs.git`. If you already have the clone, get the newest files with `git -C nextia-learning-labs pull`. Without Git, download [the ZIP file of this repository](https://github.com/usmanahmed99/nextia-learning-labs/archive/refs/heads/main.zip) and unzip it in `~/projects`.
2. Keep your own project: rename `~/projects/ticket-api` to `ticket-api-old` (Windows: `Rename-Item ticket-api ticket-api-old`).
3. Copy the snapshot into a new `ticket-api` folder, and take your `.env` and `secrets/` with you:

   ```sh
   cp -R nextia-learning-labs/C25/snapshots/end-of-m03 ticket-api
   cp ticket-api-old/.env ticket-api/ && cp -R ticket-api-old/secrets ticket-api/
   ```

   On Windows, in PowerShell: `Copy-Item -Recurse nextia-learning-labs\C25\snapshots\end-of-m03 ticket-api`, then `Copy-Item ticket-api-old\.env ticket-api\` and `Copy-Item -Recurse ticket-api-old\secrets ticket-api\`. Compare your `.env` with the snapshot's `.env.example`: a later module adds settings.
4. Make the virtual environment, bring the database to this stage and run the tests:

   ```sh
   cd ticket-api
   python3 -m venv .venv
   source .venv/bin/activate              # Windows: .venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   docker compose up -d db azurite cache
   python -m scripts.load --reset
   python -m pytest
   ```

   A database that has migrations from a later snapshot cannot go back: to go back to an earlier snapshot, delete the database first (`docker compose down --volumes`).

## Tested

The snapshots are made by a script from one reference project. Each one was checked with Python 3.12 on macOS (Apple silicon), in a new virtual environment, with a new PostgreSQL database (pgvector/pgvector:0.8.7-pg18-trixie) and an empty Valkey (valkey/valkey:9.1.2-trixie): lint, tests and the stage's first commands, with the snapshot's own simulated provider, API and worker. Windows and Linux are not tested.
