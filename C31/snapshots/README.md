# The course project, stage by stage

Each folder is the whole project at one point of the course. Copy the one that your lesson names, then set it up:

```sh
cp -R snapshots/end-of-m03 observable-workflow
cd observable-workflow
python3 -m venv .venv
source .venv/bin/activate                         # Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
```

PowerShell: `Copy-Item -Recurse snapshots\end-of-m03 observable-workflow`.

| Folder | What it adds | Tests |
|---|---|---|
| `start` | The agents course's workflow, live: it sends the reply, closes the ticket and writes one log line | 72 |
| `end-of-m01` | `obs` (read saved telemetry), the replayed week's telemetry, the audit store's reader, Grafana's compose file | 76 |
| `end-of-m02` | OpenTelemetry: one span per run, file export, the run clock, the pinned names; the Collector's configurations | 81 |
| `end-of-m03` | Model, tool and write spans, the idempotency key, approvals as two linked traces, handoffs, MCP, the gateway | 85 |
| `end-of-m04` | The five agent failure patterns (`obs find`), the TraceQL sheet, the events of a run | 92 |
| `end-of-m05` | Cost on every span and run, with the price table's date; `obs cost` | 95 |
| `end-of-m06` | The audit trail: a fixed schema, an append-only store with a hash chain, the audit story | 103 |
| `end-of-m07` | Service levels and alerts (`obs slo`, `obs alerts`) with the same rules as Grafana's | 108 |
| `end-of-m08` | Langfuse as a second destination; the course end | 110 |

The tests were run with Python 3.12 on macOS. One test needs the optional MCP package (`requirements-mcp.txt`); it
is skipped when the package is not there. Delete `work/` to start a stage again.
