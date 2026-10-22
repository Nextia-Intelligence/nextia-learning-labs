# ai-estate

The project of the course *Governing AI Agents: Gateways, Registries and Controls* (Nextia Learning). Larkfield's
AI estate on its way under governance: apps ask for a **capability** instead of a model, every agent
is **registered** with its own identity, and a **model gateway** and a **tool gateway** check, limit and record every
call.

You need no account and no key. The models' answers are **real recordings** of earlier courses, replayed by a
**provider simulator** on your computer. Outages, slow answers and the network's egress log are **simulated**,
and the weekly digest script is a **constructed** practice case.

## What runs on your computer

| Service | Command | Port |
|---|---|---|
| provider simulator | `python -m provsim` | 8320 |
| control plane: tokens, keys, configuration, approvals | `python -m estate serve` | 8321 |
| gateway front door (what the apps call) | `python -m gateway.front` | 8322 |
| gateway replicas a, b, c | `python -m gateway --replica a` | 8323, 8324, 8325 |
| tool gateway (it starts the two MCP servers) | `python -m toolgate` | 8326 |

`python -m estate up` starts them all (and `python -m estate down` stops them).

| Folder | What it is |
|---|---|
| `provsim/` | the provider simulator and the recordings it answers with |
| `apps/` | the estate's apps as replayers of their real recorded requests, and the weekly digest script |
| `resolver/` | the agents course's support workflow |
| `support_mcp/` | the MCP course's support server |
| `estate/` | the estate's command line, `python -m estate` |
| `docs/` | worked examples |
| `config/` | the capability catalog, the models, the providers and the data classes; teams and people; the gateway's settings; the tools and the approval policy |
| `registrations/` | each app's registration form |
| `evaluations/` | each consumer's evaluation, for the remap gate |
| `gateway/` | the model gateway |
| `toolgate/`, `orders_mcp/` | the tool gateway, and the order systems' MCP server behind it |
| `evidence/` | the replayed month's bill, expense, egress log and estate report |
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
python -m estate init
for f in registrations/*.yaml; do python -m estate register "$f"; done
for a in support-workflow support-mcp orders-mcp; do python -m estate review "$a" --next 2026-12-01; done
for a in ticket-triage support-workflow doc-assistant release-judge helpdesk-assistant; do
  python -m estate credentials issue "$a"
done
python -m estate up
python -m apps.replay ticket-triage --units 5 --via gateway
```

PowerShell: `Get-ChildItem registrations\*.yaml | ForEach-Object { python -m estate register $_.FullName }`, and
the same `foreach` for the reviews and the credentials. A variable for one session: `$env:NAME = "value"`.

The support workflow through both gateways; a person approves through the platform:

```sh
RESOLVER_PROVIDER=gateway RESOLVER_TOOLS=gateway python -m resolver run T-90103 --variant agent_structured --model strong-reasoning
RESOLVER_PROVIDER=gateway RESOLVER_TOOLS=gateway python -m resolver approve T-90103-agent_structured-strong-reasoning-1 --as agent --approver usr-sam
python -m estate policy test
python -m estate usage
```

Stop and reset:

```sh
python -m estate down
python -m estate reset          # deletes state/: the registry, the keys, the usage records, the practice database
```

## Commands

`python -m estate --help` lists every command of this stage. The provider simulator has its own:
`python -m provsim bill`, `egress`, `control`.

## Tested

With Python 3.12.13 on macOS (Apple silicon). The commands for Windows (PowerShell) and Linux are written, not
tested by the course. Where each copied file comes from: `PROVENANCE.md`.
