# Gateways compared: the comparison sheet

Our gateway's column comes from this project's code. Every other column is filled **from that product's own
current documentation**, with the date you checked it, a link for each cell, and "not found in the
documentation" where the documentation says nothing. Do not fill a cell from memory or from a blog post.

| Feature | This course's gateway | LiteLLM proxy | Envoy AI Gateway | Cloudflare AI Gateway | Azure API Management (AI gateway) |
|---|---|---|---|---|---|
| Date checked | (the code) | | | | |
| Registration before the first call | yes: the registry; unregistered agents are refused (`not_registered`) | | | | |
| One identity per agent | yes: client credentials, RS256 tokens for 10 minutes | | | | |
| Capability names instead of models | yes: the catalog, with contracts and fallbacks | | | | |
| Feature checks in the contract | yes: `estate catalog check`; tools refused for strong-reasoning | | | | |
| Budgets per agent and team | yes: monthly, hard stop, warning at 80% | | | | |
| Rate limits and token quotas | yes: per minute, per day, shared by the replicas | | | | |
| Step limit per run | yes: `X-Run-Id`, `max_calls_per_run` | | | | |
| Guardrails | two simple rules (card numbers, secrets) and your own patterns | | | | |
| Tool control (MCP) | yes: the tool gateway, tools per agent, approval policy | | | | |
| Kill switches | yes: writes, a tool, a capability, everything; suspend, drain, revoke | | | | |
| OpenTelemetry | optional spans with GenAI attribute names | | | | |
| Self-hosted | yes: all of it on your computer | | | | |
| Licence | MIT | | | | |
| What it needs to run | Python and SQLite | | | | |
| Supply-chain risk | 10 pinned packages (requirements.txt) | | | | |

What to look for in each product's documentation: how an app authenticates (and whether a key is per agent or
per team), whether a model alias can hide a model change, what happens when the product itself is down, where
the usage records are stored and for how long, whether prompt text is kept, and which parts are under which
licence (some products have open and paid parts).
