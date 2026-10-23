# TraceQL queries for the support workflow

Paste a query in Grafana: Explore, data source Tempo, query type TraceQL. Each query finds traces, not runs: a run that waited for a person has two traces, joined by a span link. The same patterns, computed on saved telemetry, are in `obs/flags.py` (`python -m obs find ...`).

| Name | Query | What it finds | Watch out |
|---|---|---|---|
| runs of one ticket | `{ span.larkfield.ticket.id = "T-90104" }` | every trace of ticket T-90104 (both traces of a run) |  |
| loop | `{ span.larkfield.stop_reason =~ "repeated_call\|max_steps" }` | runs stopped by a loop limit |  |
| many calls to one tool | `{ span.gen_ai.tool.name = "get_order" } \| count() > 2` | traces with 3 or more get_order calls |  |
| hidden tool error | `{ span.larkfield.tool.kind = "read" && status = error } && { span.larkfield.outcome = "resolved" }` | a read failed and the run was closed as resolved | also finds errors that a later call repaired: open each trace |
| duplicate write | `{ span.gen_ai.tool.name = "request_refund" && span.larkfield.write.outcome =~ "done\|timeout" } \| count() > 1` | two refund calls in one trace that may both have changed the data | a timeout BEFORE the write also counts: check the payment system |
| write without an approval | `{ rootName !~ "approve.*" && span.larkfield.tool.kind = "write" && span.gen_ai.tool.name != "send_reply" }` | a write in a trace that does not start with a person's decision | 0 in the course's week: every write is in an approval trace |
| no action | `{ span.larkfield.outcome = "resolved" && span.larkfield.writes_done = 0 } && { span.larkfield.reply.status = "failed" }` | closed as resolved, nothing written and the reply failed |  |
| injected input | `{ span.larkfield.input.injection = true }` | runs whose input carried an injected instruction | whether a write followed is in the run's SECOND trace: TraceQL cannot join two traces; follow the link |
| slow model calls | `{ span.gen_ai.operation.name = "chat" && duration > 5s }` | model calls longer than 5 seconds |  |
| expensive runs | `{ span.gen_ai.operation.name =~ "invoke_agent\|invoke_workflow" && span.larkfield.cost.usd > 0.01 }` | runs that cost more than 1 cent |  |
| a model's runs | `{ span.gen_ai.request.model = "gemma3:4b" && span.gen_ai.operation.name = "invoke_agent" }` |  |  |
