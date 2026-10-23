# observable-workflow (end-of-m02)

The project of the course *Observability for AI Agents: Traces, Costs and Audit Trails*, as it is at this point
of the course. It is Larkfield's support-resolution workflow from the course *AI Agents and Workflow
Orchestration*, now live: it sends the reply and closes the ticket. You need no account and no key: every model
decision is a real recording, replayed, and every change goes to a practice database on your computer.

New: OpenTelemetry. `resolver/telemetry.py` sets it up (file export to `work/telemetry` by default),
`resolver/conventions.py` names every attribute, and each run is one span. The Collector's configurations are
in `collector/`, and the replayed week can be made again (`python -m scenarios week`).

```sh
python -m resolver run T-80008
python -m obs trace T-80008
python -m obs check-redaction work/telemetry
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
