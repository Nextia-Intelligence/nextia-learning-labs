# Failure modes by risk tier (config/gateway.yaml)

What a gateway replica does when one of its own controls cannot run: its configuration is older than
`max_stale_seconds` (the control plane has not answered), or the usage store is unreachable (budgets cannot be
counted across replicas). Provider outages are different: they go to the mapping's fallbacks.

| Risk tier | Mode | While the control is down | What fail open means here |
|---|---|---|---|
| low (document assistant) | fail open | calls pass with the last configuration, marked `x-gateway-degraded` | each replica counts from the last total it read plus what it served itself, so with three replicas an agent can spend up to three times the budget it had left; guardrails still run (they are code in the replica); a suspension made meanwhile does not arrive |
| medium (ticket triage, release judge) | fail open | the same | the same; for triage, a blocked call would send tickets to a person, which is slower but safe |
| high (support workflow, tool servers) | fail closed | calls are refused: 503 `control_unavailable` | not used: a write without every control is not allowed; the workflow hands its tasks to people |

A registration's long form may set its own failure mode (`long_form.failure_mode`): it wins over the tier's.
