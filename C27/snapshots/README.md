# Snapshots: doc-assistant at the start and at the end of each module

Each folder here is the worked capstone of [Portfolio Capstone: Build, Evaluate and Ship an AI Product](https://learning.nextia-ai.com/courses/capstone/): `start` is the starter that you download in the first lesson; the others are the project after the last lesson of one module. On the standard track, if your project is broken or missing, copy the snapshot of the module that you finished last and continue. On the own-idea track, use them to compare: your product is yours.

| Snapshot | Use it to start | What it has (new) | Tests |
|---|---|---|---|
| [`start`](start) | Module 1 | The design-pack templates (`docs/templates/`), the setup check (`python -m scripts.check_setup`). | 10 |
| [`end-of-m01`](end-of-m01) | Module 2 | The project brief, the acceptance criteria and the evidence plan; the question bank and the held-out questions, reserved and locked (`python -m scripts.holdout check`). | 14 |
| [`end-of-m02`](end-of-m02) | Module 3 | The data pack (`data/`), the parser, the core schema (`migrations/001_core.sql`), Compose with PostgreSQL, the architecture and the threat and cost review. | 23 |
| [`end-of-m03`](end-of-m03) | Module 4 | The API, ingestion as jobs, the answer pipeline with citations and traces, the plain page, recorded answers. Nobody signs in yet. | 62 |
| [`end-of-m04`](end-of-m04) | Module 5 | Sign-in (the practice identity provider), memberships and roles, row-level security, failure handling, the evidence view, deletion. | 95 |
| [`end-of-m05`](end-of-m05) | Module 6 | The evaluation and the isolation checks; keyword search next to the vectors (the one improvement); the evaluation report. | 104 |
| [`end-of-m06`](end-of-m06) | Module 7 and the final assignment | The image, Compose for the whole demo, the CI workflow, the smoke test, usage limits, the runbook; Module 7's documents (README, demo script, portfolio checklist, reflection, marking rubric). The course-end project. | 108 |

The test counts include the tests that need the database (`TEST_DATABASE_URL` in `.env`); without it, they are skipped.

## What a snapshot does not have

- `.env` (make it from `.env.example`) and `.idp/` (`python -m idp init`, from Module 4).
- The virtual environment `.venv`, the models (they download on first use) and your database (it lives in Docker).

## Use a snapshot

1. Get the files: clone this repository (`git clone https://github.com/Nextia-Intelligence/nextia-learning-labs.git`), or download [its ZIP file](https://github.com/Nextia-Intelligence/nextia-learning-labs/archive/refs/heads/main.zip).
2. Copy the snapshot to your projects folder, for example as `~/projects/doc-assistant`. Keep your own project under another name first.
3. Follow the snapshot's `README.md`: it has the commands for its stage.
