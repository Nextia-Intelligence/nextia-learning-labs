# observable-workflow (end-of-m03)

The project of the course *Observability for AI Agents: Traces, Costs and Audit Trails*, as it is at this point
of the course. It is Larkfield's support-resolution workflow from the course *AI Agents and Workflow
Orchestration*, now live: it sends the reply and closes the ticket. You need no account and no key: every model
decision is a real recording, replayed, and every change goes to a practice database on your computer.

New: the model calls, tool calls, writes and reconciles are spans; an approval is a second trace with a link to
the first; the two workers carry the trace context; the order lookup can go through an MCP server; the model
calls can go through the agents governance course's gateway (`gateway-lab.md`, `vendor/ai-estate/`).

```sh
python -m resolver run T-90104 --variant agent_structured --model chat-strong
python -m resolver approve T-90104-agent_structured-chat-strong-1 --as agent --fault request_refund:timeout_after_write --naive-retry
python -m obs trace T-90104
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
