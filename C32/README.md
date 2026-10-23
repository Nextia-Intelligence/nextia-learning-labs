# Governing AI Agents: Gateways, Registries and Controls

Files for the course [Governing AI Agents: Gateways, Registries and Controls](https://learning.nextia-ai.com/courses/agent-governance/).

| Folder | What it has |
|---|---|
| [`snapshots/`](snapshots) | The course project `ai-estate`: `start` (Larkfield's AI estate before governance; download it in the first lesson) and the project at the end of each module. Code MIT; data CC0. |
| [`data/`](data) | The recorded model answers that the provider simulator gives (from the earlier courses), the apps' recorded request streams, and a [dataset card](data/dataset.md). CC0. |
| [`cs1/`](cs1) | Case study [A capability catalog from public evaluation results](https://learning.nextia-ai.com/courses/agent-governance/m08/capability-catalog-from-public-evaluations/): the project `public-catalog` (`starter.zip` to start, `finished.zip` to compare) and its [dataset card](cs1/dataset.md). |
| [`cs2/`](cs2) | Case study [Contain a runaway agent](https://learning.nextia-ai.com/courses/agent-governance/m08/contain-a-runaway-agent/): the project `runaway-replay` (`starter.zip`, `finished.zip`) and its [dataset card](cs2/dataset.md). |
| [`cs3/`](cs3) | Case study [Review public MCP servers for registration](https://learning.nextia-ai.com/courses/agent-governance/m08/review-public-mcp-servers-for-registration/): the project `mcp-intake` (`starter.zip`, `finished.zip`) and its [dataset card](cs3/dataset.md). |

You need no account, no key and no money. Everything runs on your computer with Python: the provider simulator, the control plane, the model gateway and its replicas, the tool gateway and its two MCP servers. Every model answer is a real recording of an earlier course, replayed by the simulator; the outages, the egress log and the second Azure region are simulated, and the weekly digest script is a made-up practice case. All of Larkfield's data is made up: no real customer, ticket or order is in it, and every key in the files is a practice key that only the simulator accepts.

## Case studies

Each case study is a project of its own. Unzip `starter.zip`, follow the case study's page, then compare your work with `finished.zip`. The case studies use public data; each dataset card names the source, its licence and what was kept.

## Tested

Tested with Python 3.12 on macOS (Apple silicon): every snapshot, in a new virtual environment, passes its lint and its tests, and the stage's first commands run, with every service on its own free port. Windows and Linux are not tested; the commands for them are in each snapshot's README.
