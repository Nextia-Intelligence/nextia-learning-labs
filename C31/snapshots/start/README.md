# observable-workflow (start)

The project of the course *Observability for AI Agents: Traces, Costs and Audit Trails*, as it is at this point
of the course. It is Larkfield's support-resolution workflow from the course *AI Agents and Workflow
Orchestration*, now live: it sends the reply and closes the ticket. You need no account and no key: every model
decision is a real recording, replayed, and every change goes to a practice database on your computer.

This is the starting point: the workflow writes one log line per closed ticket (`work/logs/workflow.log`), and
nothing else. `data/logs/week.log` is the log of last week, as Larkfield has it today.

```sh
python -m resolver run T-80008
python -m resolver run T-90104 --variant agent_structured --model chat-strong
python -m resolver approve T-90104-agent_structured-chat-strong-1 --as agent
cat work/logs/workflow.log                      # PowerShell: Get-Content work\logs\workflow.log
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
