# ai-estate

The project of the course *Governing AI Agents: Gateways, Registries and Controls* (Nextia Learning). Larkfield's
AI estate on its way under governance: apps ask for a **capability** instead of a model.

You need no account and no key. The models' answers are **real recordings** of earlier courses, replayed by a
**provider simulator** on your computer. Outages, slow answers and the network's egress log are **simulated**,
and the weekly digest script is a **constructed** practice case.

## What runs on your computer

| Service | Command | Port |
|---|---|---|
| provider simulator | `python -m provsim` | 8320 |

`python -m estate up` starts them all (and `python -m estate down` stops them).

| Folder | What it is |
|---|---|
| `provsim/` | the provider simulator and the recordings it answers with |
| `apps/` | the estate's apps as replayers of their real recorded requests, and the weekly digest script |
| `resolver/` | the agents course's support workflow |
| `support_mcp/` | the MCP course's support server |
| `estate/` | the estate's command line, `python -m estate` |
| `docs/` | worked examples |
| `config/` | the capability catalog, the models, the providers and the data classes |
| `registrations/` | each app's registration form (drafts: who uses which capability, and its evaluation) |
| `evaluations/` | each consumer's evaluation, for the remap gate |
| `data/` | the data and its card (`data/dataset.md`) |

## Set up

```sh
python3.12 -m venv .venv
source .venv/bin/activate                  # Windows (PowerShell): .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Start the estate, and the capability catalog

```sh
python -m estate up
python -m estate catalog list
python -m estate catalog show strong-reasoning
python -m estate catalog check
python -m estate remap gate strong-reasoning --to azure/chat-small --param reasoning_effort=none
python -m estate down
```

## Commands

`python -m estate --help` lists every command of this stage. The provider simulator has its own:
`python -m provsim bill`, `egress`, `control`.

## Tested

With Python 3.12.13 on macOS (Apple silicon). The commands for Windows (PowerShell) and Linux are written, not
tested by the course. Where each copied file comes from: `PROVENANCE.md`.
