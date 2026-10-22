# ai-estate

The project of the course *Governing AI Agents: Gateways, Registries and Controls* (Nextia Learning), at the
start of the course: **Larkfield's AI estate before governance**. The apps that earlier courses built each call
the model provider their own way, with a shared team key or a personal key, and the provider's bill is the only
record of what they used.

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
| `data/` | the data and its card (`data/dataset.md`) |

## Set up

```sh
python3.12 -m venv .venv
source .venv/bin/activate                  # Windows (PowerShell): .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
```

## Start the estate

```sh
python -m estate up
python -m apps.replay ticket-triage --units 5
python -m apps.replay support-workflow --units 2
python -m apps.replay doc-assistant --units 3
python -m apps.replay release-judge --units 3
python apps/digest/weekly_digest.py
python -m provsim bill
python -m provsim egress
python -m estate down
python -m estate reset
```

## Commands

`python -m estate --help` lists every command of this stage. The provider simulator has its own:
`python -m provsim bill`, `egress`, `control`.

## Tested

With Python 3.12.13 on macOS (Apple silicon). The commands for Windows (PowerShell) and Linux are written, not
tested by the course. Where each copied file comes from: `PROVENANCE.md`.
