# The gateway's view and the app's view

The agents governance course gives Larkfield a model gateway: every model call of every agent passes through it,
and it records who called, which capability, which model answered, the tokens and the cost. This project carries a
pinned copy of that course's estate in `vendor/ai-estate/` (see `vendor/ai-estate/PINNED.md`), so you can run the
workflow through the gateway and compare the gateway's records with the workflow's own traces.

You need the estate's packages too:

```sh
python -m pip install -r requirements-gateway.txt
```

Start the estate (in a second terminal, from `vendor/ai-estate`; it uses the ports 8320 to 8326):

```sh
cd vendor/ai-estate
python -m estate init
python -m estate register registrations/support-workflow.yaml
python -m estate review support-workflow --next 2026-12-01
python -m estate credentials issue support-workflow
python -m estate config publish --note "the registrations"
python -m estate up
```

PowerShell: the same commands (`cd vendor\ai-estate`).

Run a ticket through the gateway (from the project folder). The model is a capability name now:

```sh
RESOLVER_PROVIDER=gateway ESTATE_STATE=vendor/ai-estate/state python -m resolver run T-90103 --variant agent_structured --model strong-reasoning
python -m obs trace T-90103
```

PowerShell: `$env:RESOLVER_PROVIDER = "gateway"; $env:ESTATE_STATE = "vendor\ai-estate\state"` before the command.

Each `chat` span now has `larkfield.gateway.model` (the model that answered, from the gateway's answer header),
`larkfield.gateway.request_id` and `larkfield.gateway.cost_usd`. The gateway's own records are in its usage store:

```sh
cd vendor/ai-estate
python -m estate usage --by model
```

Stop the estate with `python -m estate down` (in `vendor/ai-estate`).

The saved result of the course team's run (the 70 tasks through the gateway) is in `data/telemetry/gateway/`:
the traces, and `gateway-usage.json`, the gateway's records of the same calls. Compare them with
`python -m obs gateway data/telemetry/gateway/gateway-usage.json --data data/telemetry/gateway`.
