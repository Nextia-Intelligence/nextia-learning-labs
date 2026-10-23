# Where the files come from

- `resolver/`, `data/` (except `data/telemetry/`, `injection_markers.json`, `people.json`), `recordings/`, `tests/`
  (the files without telemetry in their name: `test_adversarial.py` ... `test_workflow.py`, `conftest.py`,
  `scripted.py`), `LICENSE`: the project of *AI Agents and Workflow Orchestration* at its course end (its labs
  folder `snapshots/end-of-m06`; site repository commit e922d890). Unchanged, except: `runner.py` (the run span), `tools.py`
  (the tool span; optional MCP), `execute.py` (write and reconcile spans), `agent.py` (the two workers' spans and the
  handoff message), `state.py` (a `telemetry` field), `config.py` (the gateway provider), `__main__.py` (`run` and
  `approve` use `live.py`: the reply is sent, the run is closed). The recordings and prompts are byte for byte the
  same, so every recorded decision replays exactly.
- New in this course: `resolver/telemetry.py`, `conventions.py`, `observe.py`, `live.py`, `helpdesk.py`,
  `gateway.py`, `mcp_tools.py`, `mcp_server.py`; `auditstore/`, `obs/`, `scenarios/`, `collector/`, `grafana/`,
  `data/telemetry/`, the other tests.
- `resolver/mcp_server.py` follows the agents course's optional MCP example (its labs folder `optional/mcp-example`).
- `resolver/gateway.py` follows the agents governance course's `resolver/platform.py` (commit 16d18f03), with the
  real trace context instead of a traceparent made from the run ID.
- `vendor/ai-estate/`: the agents governance course's project at commit 16d18f03, unchanged (`PINNED.md`).
