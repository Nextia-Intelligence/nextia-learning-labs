# observable-workflow (end-of-m07)

The project of the course *Observability for AI Agents: Traces, Costs and Audit Trails*, as it is at this point
of the course. It is Larkfield's support-resolution workflow from the course *AI Agents and Workflow
Orchestration*, now live: it sends the reply and closes the ticket. You need no account and no key: every model
decision is a real recording, replayed, and every change goes to a practice database on your computer.

New: service levels and alerts. `python -m obs slo` and `python -m obs alerts` use the alert rules of
`grafana/alerts/` on saved telemetry; the same rules are Grafana's.

```sh
python -m obs slo --data data/telemetry/week
python -m obs alerts --data data/telemetry/week
python -m obs alerts --data data/telemetry/healthy-week
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
