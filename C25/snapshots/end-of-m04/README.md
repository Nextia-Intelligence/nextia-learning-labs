# ticket-api: operating an AI service

The project of [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/) (Nextia Learning). It is the ticket service of the scaling course, now live for Larkfield's customers. Every new ticket is triaged by the help desk's assistant (the one that [Evaluating and Testing AI Systems](https://learning.nextia-ai.com/courses/evals/) tested): the team, whether a person must handle the ticket, and a draft reply. In this course you make the service operable, one module at a time.

All the data is made up for the course: no real customer wrote a ticket. The AI provider is **simulated** on your computer. For the 268 practice tickets (`data/practice/tickets.jsonl`), it answers with **real recorded answers** of a hosted model (prompt v2 and prompt v3, recorded by the evaluation course): those answers are *replayed*. Any other message gets a *simulated* answer: its time, tokens and how often it is cut off come from the same recordings, but its text is a template.

## What you need

- Python 3.12 or later.
- Docker (Docker Desktop on Windows and macOS) for PostgreSQL 18 with pgvector, Azurite and Valkey, as in the scaling course. From Module 3, optionally, the Grafana stack (one container, about 1.3 GB of memory while it runs).

You do not need an account, a key or money.

## Set up

macOS and Linux:

```sh
cp .env.example .env              # then change the password in .env (three places)
mkdir -p secrets && echo "local-practice-key" > secrets/api_key.txt
docker compose up -d db azurite cache
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m scripts.load --reset    # the migrations, then the small data
python -m pytest
```

Windows (PowerShell):

```powershell
Copy-Item .env.example .env       # then change the password in .env (three places)
New-Item -ItemType Directory -Force secrets; Set-Content secrets\api_key.txt "local-practice-key"
docker compose up -d db azurite cache
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m scripts.load --reset
python -m pytest
```

Then, in three terminals (venv active in each):

```sh
python -m simulator               # the simulated AI provider, http://127.0.0.1:8300/v1
fastapi dev                       # the API, http://127.0.0.1:8000/docs
python -m ticket_api.worker       # the worker: it triages the queued tickets
```

Send practice tickets and watch them: `python -m scripts.practice --tickets 20 --rate 2`, then `python -m scripts.queue_watch`.

**Reset:** `python -m scripts.load --reset` loads the data again (new tickets start at T-500001); `docker compose down --volumes` deletes the database.

## Commands

Module 1: what is operated, objectives, owners:

```sh
python -m ops summary FILE            what a saved telemetry file holds
python -m ops inventory               what the service depends on, and who owns it
python -m ops slo FILE                SLIs against SLOs, with error budgets
```

Module 2: versions and lineage:

```sh
python -m ops release build --prompt assistant-v2 --write   a release manifest
python -m ops release diff OLD NEW                          what changed
python -m ops release verify ID                             do the files still match it?
python -m ops trace TICKET FILE                             from an answer to its versions
python -m ops experiments [EXP-001]                         experiment records
```

Module 3: telemetry:

```sh
python -m ops waterfall FILE --ticket T-500123    one trace: time and cost of each step
python -m ops quality FILE [--by release]         outcomes, tokens, time, cost by version
python -m ops privacy FILE                        text, e-mail addresses, size
python -m ops prune FILE --days 30                retention
docker compose --profile observability up -d observability   Grafana (optional)
```

Module 4: drift, delayed labels, LLM and RAG checks:

```sh
python -m ops drift FILE --at MINUTE              input and prediction drift (PSI, chi-square)
python -m ops labels FILE                         agents' reviews and proxy signals
python -m ops rag FILE                            old sources, model versions
python -m scripts.send_reviews --delay 120 --follow   agents' reviews, later
python -m scripts.reindex [--check]               the answers' retrieval index
```

## Files added in this course

| File | What it does |
|---|---|
| `ticket_api/assistant.py, ticket_api/prompts/` | the triage step: prompt files, policy, output schema |
| `migrations/015_triage.sql` | the triage task, the assistant's teams, needs_human |
| `simulator/replay.py, recorded_assistant.jsonl.gz` | real recorded answers, replayed |
| `scripts/practice.py, data/practice/tickets.jsonl` | practice tickets with their labels |
| `ops/` | the ops tool (standard library only) |
| `operations/inventory.toml, slos.toml, service-brief.md` | components, owners, objectives, severity levels |
| `ticket_api/releases.py, operations/releases/` | release manifests; RELEASE_ID |
| `migrations/016_release_ids.sql` | the release ID on every AI result |
| `operations/experiments/` | experiment records |
| `ticket_api/telemetry.py, docs/telemetry.md` | OpenTelemetry: traces, metrics, logs, redaction, sampling |
| `migrations/017_job_trace_context.sql` | the job continues the request's trace |
| `observability/` | the Grafana stack: dashboards and alert rules from files |
| `ticket_api/reviews.py, migrations/018_ticket_reviews.sql` | agents' reviews (delayed labels) |
| `migrations/019_answer_index.sql, scripts/reindex.py, update_document.py` | the retrieval index and a stale index |
| `ops/stats.py` | PSI, chi-square, Wilson interval |

## Saved telemetry (no Docker needed)

The course team recorded the practice scenarios on this project, with the Grafana stack, and
saved their telemetry. Download them from the course's labs repository (`C25/data/`) and read
them with `python -m ops`: every lesson works from these files.
