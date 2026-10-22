# Governing AI Agents: Gateways, Registries and Controls

Files for the course [Governing AI Agents: Gateways, Registries and Controls](https://learning.nextia-ai.com/courses/agent-governance/).

| Folder | What it has |
|---|---|
| [`snapshots/`](snapshots) | The course project `ai-estate`: `start` (Larkfield's AI estate before governance; download it in the first lesson) and the project at the end of each module. Code MIT; data CC0. |
| [`data/`](data) | The recorded model answers that the provider simulator gives (from the earlier courses), the apps' recorded request streams, and a [dataset card](data/dataset.md). CC0. |

You need no account, no key and no money. Everything runs on your computer with Python: the provider simulator, the control plane, the model gateway and its replicas, the tool gateway and its two MCP servers. Every model answer is a real recording of an earlier course, replayed by the simulator; the outages, the egress log and the second Azure region are simulated, and the weekly digest script is a made-up practice case. All of Larkfield's data is made up: no real customer, ticket or order is in it, and every key in the files is a practice key that only the simulator accepts.

## Tested

Tested with Python 3.12 on macOS (Apple silicon): every snapshot, in a new virtual environment, passes its lint and its tests, and the stage's first commands run, with every service on its own free port. Windows and Linux are not tested; the commands for them are in each snapshot's README.
