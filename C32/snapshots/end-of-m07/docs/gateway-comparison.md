# Gateways compared: the comparison sheet

Our gateway's column comes from this project's code. Every other column comes **from that product's own
documentation**, with a source for each cell (the numbers in brackets, listed under the table), and "not found"
where the documentation says nothing. Do not fill a cell from memory or from a blog post.

**Products change every few weeks.** The row "Documentation read" names the version that the course team read.
Before you decide anything, check each product's current documentation again, and change the cells that changed.

Each cell starts with one word that a script can read: **yes**, **partly**, **no** or **not found**. The rest of
the cell says what the documentation says. "Not found" means only that the course team did not find it in the
documentation: it is not a promise that the product cannot do it.

| Feature | This course's gateway | LiteLLM proxy | Agent Router (formerly Envoy AI Gateway) | Cloudflare AI Gateway | Azure API Management (AI gateway) |
|---|---|---|---|---|---|
| Documentation read | the code (ai-estate 1.0.0) | documentation of v1.106.2 | documentation of v1.2 | the current documentation (a managed service has no version) | the current documentation (some AI features are in preview) |
| Registration before the first call | yes: the registry (owner, purpose, risk tier, data classes, review date); unregistered agents are refused (`not_registered`) | partly: a key has an owner (`user_id`) and a team; agents can be added with a name and an address; no purpose, risk tier or review date [L1] | not found: access is set in Kubernetes route and security-policy resources [E1] | not found: Cloudflare Access policies say which users may call [CF1] | partly: products and subscriptions; with "requires approval", an administrator accepts each subscriber; no purpose, risk tier or review date [A1] |
| One identity per agent | yes: client credentials, RS256 tokens for 10 minutes | yes: a virtual key per user, team or agent; sign-in with JWT/OIDC is in the enterprise edition [L2] | partly: the caller's authentication is Envoy Gateway's (API keys, OAuth, JWT, external authorisation) [E2] | partly: gateway tokens are account-wide Cloudflare API tokens; one identity per user through Cloudflare Access [CF2] | yes: a subscription key per consumer, or Microsoft Entra ID or any JWT checked by a policy [A2] |
| Capability names instead of models | yes: the catalog, with contracts and fallbacks | yes: `model_name` is the name that apps use; model groups and aliases [L3] | yes: model name virtualization (`modelNameOverride`) [E3] | yes: dynamic routes, called as `dynamic/<name>`, with versions [CF3] | yes (preview): the unified model API's aliases [A3] |
| An OpenAI-compatible endpoint | yes: `/v1/chat/completions`, `/v1/embeddings` | yes: "one OpenAI-compatible endpoint" [L4] | yes: "an OpenAI-compatible router" [E4] | yes: the compatible endpoint (`/compat/chat/completions`) [CF4] | yes (preview): "a single OpenAI-compatible endpoint" [A3] |
| Feature checks in the contract | yes: `estate catalog check`; tools refused for strong-reasoning | not found: the pre-call checks look at the context window and the region [L5] | not found [E3] | not found: only the request format is checked [CF3] | not found [A3] |
| Fallbacks | yes: the same model in a second region; on 429, 5xx and time-outs; a breaker | yes: ordered fallbacks across models and providers, retries, cool-downs [L6] | yes: a priority list of backends, with Envoy Gateway's retry policy [E5] | yes: fallbacks, and up to five retries [CF5] | yes: backend pools, a circuit breaker (not in the Consumption tier), a retry policy [A4] |
| Budgets per agent and team (money) | yes: monthly, hard stop, warning at 80% | yes: `max_budget` per key, user or team, with a reset period; a hard stop; needs the database [L7] | partly: token quotas, not money [E6] | yes: spend limits by provider, model or metadata (for example a team or an agent); "eventually consistent", so a burst can pass the limit [CF6] | partly: token quotas per period, not money [A5] |
| Rate limits and token quotas | yes: per minute, per day, shared by the replicas | yes: requests and tokens per minute per key, user or team; Redis shares the counters between instances [L7] | yes: token-based limits per user and model; needs Redis [E7] | partly: requests per time window for the whole gateway; no token limit found [CF7] | yes: `llm-token-limit`, tokens per minute and quotas per hour to year; not in the Consumption tier; counts are not shared between regional gateways [A5] |
| Step limit per run | yes: `X-Run-Id`, `max_calls_per_run` | yes: agent iteration budgets, `max_iterations` per session, found by a trace ID [L8] | not found [E1] | not found [CF7] | not found [A5] |
| Guardrails | yes: two simple rules (card numbers, secrets) and your own patterns | yes: personal-data masking, content filters, your own code; guardrails per key or team are in the enterprise edition [L9] | not found in the open-source project [E1] | yes: Guardrails (harmful content, prompt injection), billed as Workers AI, about 500 ms a request; data loss prevention [CF8] | yes: `llm-content-safety`, with your own Azure AI Content Safety resource [A6] |
| Tool control (MCP) | yes: the tool gateway, tools per agent, approval grants for writes | yes: an MCP gateway with permissions per key, team or user; tool policies [L10] | yes: an MCP gateway, a tool filter, allow and deny rules from the token's claims [E8] | no: not in AI Gateway; MCP server portals are a separate Cloudflare One product [CF9] | yes: exposes REST APIs as MCP servers, or passes existing MCP servers through; tools only [A7] |
| Kill switches | yes: writes, a tool, a capability, everything; suspend, drain, revoke | partly: block or unblock a key (`/key/block`) [L2] | not found: change or delete the route resources [E1] | partly: no off switch found; delete the gateway, or use Access, rate or spend limits [CF10] | yes: suspend or cancel a subscription [A1] |
| OpenTelemetry | partly: optional spans with GenAI attribute names, not tested by the course | yes: traces, optional metrics, the GenAI conventions if you turn them on [L11] | yes: traces and metrics; GenAI conventions, or OpenInference by default [E9] | yes: traces to OpenTelemetry back ends, with gen_ai attributes [CF11] | partly: Application Insights and Azure Monitor; OpenTelemetry metrics only from the self-hosted gateway [A8] |
| Self-hosted | yes: all of it on your computer | yes: Docker, pip or Helm [L12] | yes: Kubernetes, or `aigw run` on one computer [E10] | no: a managed service only [CF4] | partly: a self-hosted gateway container in the Developer and Premium tiers; it gets its configuration from Azure [A9] |
| Where usage records are, and prompt text | one SQLite file; no prompt or answer text | spend logs in PostgreSQL; prompts not stored by default [L13] | no usage database: access logs, metrics and traces; traces include prompts by default (OpenInference) [E9] | logs on by default, with the prompts; turn off per request; how long they stay depends on the plan [CF12] | Log Analytics; prompt and answer text only if you turn it on [A10] |
| When its own store or control plane is down | yes: a failure mode per risk tier (fail open or closed after 60 s) | partly: calls fail by default; `allow_requests_on_db_unavailable` keeps keys working [L14] | partly: quota checks fail open by default if the rate-limit service is down; you can make them deny [E6] | not found: no service level for AI Gateway found [CF4] | partly: a service level per tier (none in Developer); the self-hosted gateway keeps running on its last configuration [A9] |
| Licence | MIT | MIT for the core; the `enterprise/` folder has a separate commercial licence [L15] | Apache-2.0 for all of it [E11] | a proprietary service; its core features are free, some parts are billed [CF13] | a proprietary Azure service, billed per tier [A11] |
| What it needs to run | Python and SQLite | PostgreSQL for keys and budgets; Redis for more than one instance [L16] | Kubernetes 1.32 or later and Envoy Gateway 1.9.2 or later; Redis for limits [E12] | a Cloudflare account [CF4] | an Azure subscription and an API Management instance; features depend on the tier [A11] |
| Supply-chain risk | 10 pinned packages (35 installed with what they need); a teaching project, with no security review | 22 required Python packages, 35 more for the proxy; several releases a week; versions 1.82.7 and 1.82.8 on PyPI were compromised; published security advisories [L17] | Go, 72 direct modules; a minor release about every two months; published security advisories [E13] | you run no code: the risk is the vendor's service and your account | you run no code, unless you self-host the gateway: the risk is the vendor's service and your subscription |

What to look for in each product's documentation: how an app authenticates (and whether a key is per agent or
per team), whether a model alias can hide a model change, what happens when the product itself is down, where
the usage records are stored and for how long, whether prompt text is kept, and which parts are under which
licence (some products have open and paid parts).

## Sources

LiteLLM proxy (github.com/BerriAI/litellm):

- [L1] https://docs.litellm.ai/docs/proxy/virtual_keys, https://docs.litellm.ai/docs/a2a
- [L2] https://docs.litellm.ai/docs/proxy/virtual_keys, https://docs.litellm.ai/docs/proxy/token_auth
- [L3] https://docs.litellm.ai/docs/proxy/configs, https://docs.litellm.ai/docs/proxy/model_access
- [L4] https://docs.litellm.ai/docs/simple_proxy
- [L5] https://docs.litellm.ai/docs/routing
- [L6] https://docs.litellm.ai/docs/proxy/reliability
- [L7] https://docs.litellm.ai/docs/proxy/users
- [L8] https://docs.litellm.ai/docs/a2a_iteration_budgets
- [L9] https://docs.litellm.ai/docs/proxy/guardrails/quick_start, https://docs.litellm.ai/docs/enterprise
- [L10] https://docs.litellm.ai/docs/mcp, https://docs.litellm.ai/docs/proxy/tool_policies
- [L11] https://docs.litellm.ai/docs/observability/opentelemetry_integration
- [L12] https://docs.litellm.ai/docs/proxy/docker_quick_start
- [L13] https://docs.litellm.ai/docs/proxy/cost_tracking, https://docs.litellm.ai/docs/proxy/config_settings
- [L14] https://docs.litellm.ai/docs/proxy/config_settings, https://docs.litellm.ai/docs/proxy/prod
- [L15] https://github.com/BerriAI/litellm/blob/main/LICENSE, https://docs.litellm.ai/docs/enterprise
- [L16] https://docs.litellm.ai/docs/proxy/prod
- [L17] https://github.com/BerriAI/litellm/blob/main/pyproject.toml, https://docs.litellm.ai/blog/security-update-march-2026,
  https://github.com/BerriAI/litellm/security

Agent Router, formerly Envoy AI Gateway (github.com/theagentrouter/agent-router; the API group and the `aigw`
command keep their old names):

- [E1] https://theagentrouter.ai/docs/capabilities/
- [E2] https://theagentrouter.ai/docs/capabilities/security/upstream-auth, https://theagentrouter.ai/docs/capabilities/mcp/
- [E3] https://theagentrouter.ai/docs/capabilities/traffic/model-name-virtualization
- [E4] https://theagentrouter.ai/docs/
- [E5] https://theagentrouter.ai/docs/capabilities/traffic/provider-fallback
- [E6] https://theagentrouter.ai/docs/capabilities/traffic/quota-policy
- [E7] https://theagentrouter.ai/docs/capabilities/traffic/usage-based-ratelimiting
- [E8] https://theagentrouter.ai/docs/capabilities/mcp/
- [E9] https://theagentrouter.ai/docs/capabilities/observability/tracing, https://theagentrouter.ai/docs/capabilities/observability/metrics
- [E10] https://theagentrouter.ai/docs/getting-started/
- [E11] https://github.com/envoyproxy/ai-gateway/blob/main/LICENSE, https://theagentrouter.ai/blog/envoy-ai-gateway-is-now-agent-router
- [E12] https://theagentrouter.ai/docs/getting-started/prerequisites
- [E13] https://github.com/envoyproxy/ai-gateway/blob/main/go.mod, https://github.com/envoyproxy/ai-gateway/security

Cloudflare AI Gateway (https://developers.cloudflare.com/ai-gateway/):

- [CF1] https://developers.cloudflare.com/ai-gateway/configuration/cloudflare-access/
- [CF2] https://developers.cloudflare.com/ai-gateway/configuration/authentication/
- [CF3] https://developers.cloudflare.com/ai-gateway/features/dynamic-routing/
- [CF4] https://developers.cloudflare.com/ai-gateway/usage/chat-completion/, https://developers.cloudflare.com/ai-gateway/get-started/
- [CF5] https://developers.cloudflare.com/ai-gateway/configuration/fallbacks/, https://developers.cloudflare.com/ai-gateway/configuration/request-handling/
- [CF6] https://developers.cloudflare.com/ai-gateway/features/spend-limits/
- [CF7] https://developers.cloudflare.com/ai-gateway/features/rate-limiting/
- [CF8] https://developers.cloudflare.com/ai-gateway/features/guardrails/, https://developers.cloudflare.com/ai-gateway/features/dlp/
- [CF9] https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/
- [CF10] https://developers.cloudflare.com/ai-gateway/configuration/manage-gateway/
- [CF11] https://developers.cloudflare.com/ai-gateway/observability/otel-integration/
- [CF12] https://developers.cloudflare.com/ai-gateway/observability/logging/
- [CF13] https://developers.cloudflare.com/ai-gateway/reference/pricing/

Azure API Management (https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities):

- [A1] https://learn.microsoft.com/en-us/azure/api-management/api-management-subscriptions, https://learn.microsoft.com/en-us/azure/api-management/api-management-howto-add-products
- [A2] https://learn.microsoft.com/en-us/azure/api-management/api-management-authenticate-authorize-ai-apis
- [A3] https://learn.microsoft.com/en-us/azure/api-management/unified-model-api
- [A4] https://learn.microsoft.com/en-us/azure/api-management/backends, https://learn.microsoft.com/en-us/azure/api-management/retry-policy
- [A5] https://learn.microsoft.com/en-us/azure/api-management/llm-token-limit-policy
- [A6] https://learn.microsoft.com/en-us/azure/api-management/llm-content-safety-policy
- [A7] https://learn.microsoft.com/en-us/azure/api-management/mcp-server-overview
- [A8] https://learn.microsoft.com/en-us/azure/api-management/llm-emit-token-metric-policy, https://learn.microsoft.com/en-us/azure/api-management/how-to-deploy-self-hosted-gateway-kubernetes-opentelemetry
- [A9] https://learn.microsoft.com/en-us/azure/api-management/self-hosted-gateway-overview
- [A10] https://learn.microsoft.com/en-us/azure/api-management/api-management-howto-llm-logs
- [A11] https://azure.microsoft.com/en-us/pricing/details/api-management/
