# observable-workflow (end-of-m04)

The project of the course *Observability for AI Agents: Traces, Costs and Audit Trails*, as it is at this point
of the course. It is Larkfield's support-resolution workflow from the course *AI Agents and Workflow
Orchestration*, now live: it sends the reply and closes the ticket. You need no account and no key: every model
decision is a real recording, replayed, and every change goes to a practice database on your computer.

New: the five agent failure patterns (`obs/flags.py`, `python -m obs find`), the TraceQL sheet
(`grafana/traceql.md`) and the traces dashboard, the events of a run, and one constructed run.

```sh
python -m obs find all --data data/telemetry/week
python -m obs events R-1014-040 --data data/telemetry/week
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
