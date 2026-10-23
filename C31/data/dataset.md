# Dataset card: the replayed weeks of Larkfield's support workflow

**What it is.** Saved telemetry of Larkfield's support-resolution workflow (a made-up online garden shop): every
run as OpenTelemetry traces, the workflow's metrics, its events, and its audit trail, for one practice week of
tickets (316 runs, Monday to Sunday), the same tickets on a healthy release, one constructed run, and one run of
70 tickets through a model gateway.

**Where it comes from.**
- The model decisions are real recordings from the course *AI Agents and Workflow Orchestration* (Azure OpenAI
  `gpt-6-luna` as chat-small, `gpt-6.1-sol` as chat-strong, and `gemma3:4b` run locally), replayed. Tokens and
  latencies are the recorded ones.
- The traffic is constructed: which ticket arrives when, the releases, the people's approval times and the
  practice incidents (a slow payment service, a reply service that is down, a trial of the local model). They are
  practice incidents we caused on purpose. `week/plan.json` lists them; `week/truth.json` says which runs each one
  touched.
- The tickets, customers, orders and payments are made up for the courses. No real person wrote them.

**Files.**

| Folder | Files | What |
|---|---|---|
| `telemetry/week/` | `traces.jsonl.gz`, `logs.jsonl.gz`, `metrics.jsonl.gz` | OTLP JSON: one export request per line (the format of the OpenTelemetry Collector's file exporter; its `otlp_json_file` receiver reads it). Metrics: one cumulative snapshot per practice hour |
| | `audit.jsonl`, `audit.anchor.json`, `audit.keys.json` | The audit trail (hash-chained), its anchor, and the practice customers' pseudonym keys |
| | `plan.json`, `truth.json`, `workflow.log` | What happened when; which runs each practice incident touched; the workflow's own log lines |
| `telemetry/healthy-week/` | the same | The same tickets on the healthy release, with no incident |
| `telemetry/constructed/` | the same | One constructed run: a scripted model (not a real one) follows an injected instruction |
| `telemetry/gateway/` | `traces.jsonl`, `gateway-usage.json` | 70 tickets through the agents governance course's model gateway: the workflow's traces and the gateway's usage records |
| `logs/week.log` | | The week as the workflow's log file shows it (one line per closed ticket) |

**What is not in it.** No text of a ticket, prompt, answer or reply: only IDs, counts, codes, model and tool names.
Customer IDs are practice IDs (C-…); in the audit trail they are pseudonyms.

**Times.** The spans of the week have practice times (12 to 18 October 2026, Toronto time). The workflow's date
rules use another fixed "today" (the agents course's); do not compute dates from the spans' times.

**Licence.** CC0 1.0: you may use, change and share it with no conditions.
