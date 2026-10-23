# observable-workflow (end-of-m01)

The project of the course *Observability for AI Agents: Traces, Costs and Audit Trails*, as it is at this point
of the course. It is Larkfield's support-resolution workflow from the course *AI Agents and Workflow
Orchestration*, now live: it sends the reply and closes the ticket. You need no account and no key: every model
decision is a real recording, replayed, and every change goes to a practice database on your computer.

New: `obs`, a tool that reads saved telemetry; the telemetry of the replayed week (`data/telemetry/`); the audit
store's reader; Grafana's compose file. Your own workflow does not record telemetry yet.

```sh
python -m obs runs --data data/telemetry/week --day wed
python -m obs trace R-1014-040 --data data/telemetry/week
python -m obs audit verify --data data/telemetry/week
docker compose -f grafana/compose.yaml up -d    # optional: Grafana at http://127.0.0.1:3031
```

## Set up

```sh
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
```

Delete `work/` to start again (your practice database, your runs, your telemetry and your audit trail).
The practice data is made up; no real customer wrote it. Licence: MIT.
