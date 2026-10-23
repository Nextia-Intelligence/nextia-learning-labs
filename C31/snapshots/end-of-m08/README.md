# observable-workflow

The project of the course *Observability for AI Agents: Traces, Costs and Audit Trails* (Nextia Learning), as it is
at the end of the course. It is Larkfield's support-resolution workflow from the course *AI Agents and Workflow
Orchestration*, now live and instrumented: every run is recorded with OpenTelemetry (traces, metrics and events),
every decision, approval and change is also an audit event in a separate, hash-chained audit store, and the `obs`
tool reads all of it from files, with no Docker and no account.

You need no account and no key. Every model decision is a real recording from the agents course, replayed. The
orders, payments and help desk are a practice database on your computer. The practice incidents in the replayed week
are cases we caused on purpose.

## Set up

```sh
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
```

## A first run

```sh
python -m resolver run T-80008                  # a ticket, recorded model decisions, a reply sent
python -m obs runs                              # your runs, from work/telemetry
python -m obs trace T-80008                     # the run as a waterfall
python -m obs audit verify                      # the audit trail is intact
```

A refund that waits for a person, then the double refund of the agents course (a timeout after the write, and a
retry with a new ID):

```sh
python -m resolver run T-90104 --variant agent_structured --model chat-strong
python -m resolver approve T-90104-agent_structured-chat-strong-1 --as agent --name Sam --fault request_refund:timeout_after_write --naive-retry
python -m obs trace T-90104                     # two traces joined by a span link; the flag duplicate_write
python -m obs audit story T-90104               # the same run, told from the audit trail
python -m resolver reset --all                  # a fresh practice database, no saved runs
```

Delete `work/` to start again with no telemetry.

## The replayed week

`data/telemetry/week/` is a week of Larkfield's tickets (316 runs) with the practice incidents of the course;
`data/telemetry/healthy-week/` is the same tickets on the healthy release. `plan.json` says what happened when,
`truth.json` which runs belong to which practice incident (look at it after you have counted).

```sh
python -m obs runs --data data/telemetry/week --day wed
python -m obs find all --data data/telemetry/week
python -m obs cost --by model --data data/telemetry/week
python -m obs slo --data data/telemetry/week
python -m obs alerts --data data/telemetry/week
python -m scenarios week --out work/week        # make the week again (about 3 seconds)
```

## Grafana (optional, Docker)

```sh
python -m auditstore serve --host 0.0.0.0       # terminal 2: the audit store's door, for the Collector
docker compose -f grafana/compose.yaml up -d
OBS_EXPORT=otlp python -m resolver run T-90103  # PowerShell: $env:OBS_EXPORT = "otlp"
python -m scenarios week --otlp --out work/week # the week in compressed time: about 10 minutes
docker compose -f grafana/compose.yaml down -v
```

Grafana: http://127.0.0.1:3031 (dashboards in the folder "Support workflow"; TraceQL queries in `grafana/traceql.md`).

## Files

| Path | What it does |
|---|---|
| `resolver/` | The agents course's workflow (see `PROVENANCE.md`) with its instrumentation: `telemetry.py` (setup, exporters, the run clock), `conventions.py` (every attribute name; the GenAI conventions pinned), `observe.py` (spans, metrics and audit events of model calls, tools, writes and decisions), `live.py` (a ticket from start to close: the approval as two linked traces, the reply), `helpdesk.py`, `gateway.py`, `mcp_tools.py`, `mcp_server.py` |
| `auditstore/` | The audit event schema, the append-only hash-chained store and its verifier, the door for the Collector |
| `obs/` | The command-line tool for saved telemetry: runs, trace, find (the five failure patterns, `flags.py`), cost, events, audit, slo, alerts, check-redaction, gateway |
| `scenarios/` | The replayed week, the healthy week, the constructed run |
| `collector/` | The Collector's configurations: redaction, tail sampling for traces, audit routing; with Langfuse; without Docker |
| `grafana/` | Docker Compose for Grafana, dashboards and alert rules as files, the TraceQL sheet |
| `data/` | The agents course's practice data and the saved telemetry |
| `vendor/ai-estate/` | A pinned copy of the agents governance course's estate (its model gateway): `gateway-lab.md` |

Licence: MIT. The practice data is made up; no real customer wrote it.
