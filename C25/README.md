# MLOps and LLMOps: Operating AI in Production

Files for the course [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/).

| Folder | What it has |
|---|---|
| [`snapshots/`](snapshots) | The course project `ticket-api`: `start` (the end of [Scaling APIs and AI Workloads](https://learning.nextia-ai.com/courses/scaling/); download it in the first lesson) and the project at the end of each module. Code MIT; data CC0. |
| [`data/`](data) | Saved telemetry of the course's practice scenarios (a normal week, the prompt v3 change, a canary, a shadow run, a provider outage, a stale index, drift), the two release manifests they name, and a [dataset card](data/dataset.md). CC0. Every lesson works from these files with `python -m ops`, without Docker. |
| [`monitor-311/`](monitor-311) | Case study 1, [Monitor a model on public data that changes](https://learning.nextia-ai.com/courses/mlops/m07/monitor-a-model-on-public-data-that-changes/): a notebook and its solution, and a fixed sample of New York City's 311 service requests from January 2020 to January 2021 (NYC Open Data) with a [dataset card](monitor-311/dataset.md). Code MIT. |
| [`public-outage-pir/`](public-outage-pir) | Case study 2, [Post-incident review of a public outage](https://learning.nextia-ai.com/courses/mlops/m07/post-incident-review-of-a-public-outage/): the project `public-outage-pir` as `starter.zip` (the timeline and the review are yours to write) and `finished.zip` (the whole project), with a [dataset card](public-outage-pir/dataset.md). The timelines are our own tables of facts from the providers' published reports. Code MIT; tables and documents CC0. |

The case studies use real public data, not Larkfield's. The notebook needs an internet connection for its setup step, and it checks the SHA-256 of every file that it downloads.

You need no account, no key and no money. PostgreSQL, Valkey, the simulated AI provider and, if you want it, the Grafana stack (one Docker container) all run on your computer.

## The simulated AI provider and its real answers

The project has a small local service, `python -m simulator`, that answers like an OpenAI-compatible provider. For the course's 268 practice tickets, it answers with **real recorded answers**: the evaluation course sent those tickets to a hosted model (chat-small, model version gpt-6-luna-2026-09-22) with prompt v2 and with prompt v3 and kept every answer, with its tokens, its time and its finish reason. These answers are *replayed*. Any other message gets a *simulated* answer (its time and tokens follow the recordings; its text is a template). The lessons say which, every time.

The tickets are made up for the courses: no real customer wrote them.

## Tested

Tested with Python 3.12 on macOS (Apple silicon) with Docker Desktop, PostgreSQL 18.6 with pgvector 0.8.7, Valkey 9.1.2 and grafana/otel-lgtm 0.36.0, in a new virtual environment, a new database and an empty cache for each snapshot: every snapshot's tests pass, and the stage's first commands run. Windows and Linux are not tested.

The case-study notebook and its solution ran from a fresh start in a new virtual environment. The case-study project's script ran on the finished and the starter project, with Python's standard library only.
