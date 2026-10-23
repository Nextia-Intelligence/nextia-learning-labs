# Snapshots: ai-estate at the start and at the end of each module

Each folder here is the `ai-estate` project of [Governing AI Agents: Gateways, Registries and Controls](https://learning.nextia-ai.com/courses/agent-governance/). `start` is the project that you download in the first lesson: Larkfield's AI estate before governance, where each app calls the model provider with its own key. The others are the project after the last lesson of one module. If your project is broken or missing, copy the snapshot of the module that you finished last, and continue with the next lesson.

| Snapshot | Use it to start | What it has (new) | Tests |
|---|---|---|---|
| [`start`](start) | Module 1 | The provider simulator (`python -m provsim`) and its recordings, the apps' replayers (`python -m apps.replay`), the weekly digest script, the agents course's support workflow, the MCP course's support server. | 88 |
| [`end-of-m01`](end-of-m01) | Module 2 | The estate's command line: `python -m estate up`, `down`, `status`, `reset`; Larkfield's AI policy and the rules worksheet. | 91 |
| [`end-of-m02`](end-of-m02) | Module 3 | The capability catalog (`config/catalog.yaml`, `models.yaml`, `providers.yaml`, `data-classes.yaml`), `estate catalog`, the remap gate (`estate remap gate`) with each consumer's evaluation, draft registrations. | 104 |
| [`end-of-m03`](end-of-m03) | Module 4 | The registry (`estate register`, `review`, `suspend`, `retire`, `review-due`), one identity per agent (`estate credentials`, `token`), the control plane, the first model gateway, the apps through the gateway (`--via gateway`). | 135 |
| [`end-of-m04`](end-of-m04) | Module 5 | The whole model gateway: the usage record (`estate usage`), limits, data classes, guardrails, three replicas behind a front door, failure modes, staged configuration changes (`estate config publish --stage canary`, `watch`, `rollback`); the support workflow's model calls through the gateway. | 172 |
| [`end-of-m05`](end-of-m05) | Module 6 | The tool gateway (`python -m toolgate`) with the order systems' MCP server and the support MCP server, the approval policy (`estate policy test`), approval grants, kill switches (`estate kill`), draining; the support workflow's tools through the tool gateway; `python -m apps.helpdesk`. | 190 |
| [`end-of-m06`](end-of-m06) | Module 7 | The month's estate report (`estate report`), incidents and exceptions, finding unregistered AI (`estate discover`), the replayed month's evidence in `evidence/`. | 194 |
| [`end-of-m07`](end-of-m07) | The final assignment | The comparison sheet and the rollout plan in `docs/`, `estate adoption`. The course-end project. | 195 |

Each snapshot has only what the lessons' guided practice makes. It does not have the answers to the "Your turn" tasks.

## What a snapshot does not have

- `state/`: the registry, the keys, the usage records and the practice database. `python -m estate init` (from `end-of-m03`) makes them; `python -m estate reset` deletes them.
- The virtual environment `.venv`.

## Use a snapshot

The steps use `end-of-m03` as an example. Use the name of your snapshot.

1. Get the files. If you have Git, clone this repository once, in `~/projects`:

   ```sh
   cd ~/projects
   git clone https://github.com/Nextia-Intelligence/nextia-learning-labs.git
   ```

   If you already have the clone, get the newest files with `git -C nextia-learning-labs pull`. Without Git, download [the ZIP file of this repository](https://github.com/Nextia-Intelligence/nextia-learning-labs/archive/refs/heads/main.zip), and unzip it in `~/projects`. Its folder is `nextia-learning-labs-main`.
2. Stop your estate if it runs (`python -m estate down` in your project), and keep your own project: rename it.

   ```sh
   mv ai-estate ai-estate-old     # Windows: Rename-Item ai-estate ai-estate-old
   ```

3. Copy the snapshot into a new `ai-estate` folder:

   ```sh
   cp -R nextia-learning-labs/C32/snapshots/end-of-m03 ai-estate
   ```

   On Windows, in PowerShell: `Copy-Item -Recurse nextia-learning-labs\C32\snapshots\end-of-m03 ai-estate`.
4. Make the virtual environment and run the tests:

   ```sh
   cd ai-estate
   python3.12 -m venv .venv
   source .venv/bin/activate              # Windows: .venv\Scripts\Activate.ps1
   python -m pip install -r requirements-dev.txt
   python -m pytest
   ```

   `end-of-m03` gives `135 passed`. Then follow the snapshot's README: it starts the estate for that stage.

## Tested

The snapshots are made by a script from one reference project. Each one was checked with Python 3.12 on macOS (Apple silicon), in a new virtual environment: lint, tests, and the stage's first commands, with every service on its own free port. Windows and Linux are not tested.
