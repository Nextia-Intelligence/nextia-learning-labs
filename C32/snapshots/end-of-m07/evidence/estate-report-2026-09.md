# Larkfield AI estate report: 2026-09

Made by `python -m estate report` from the registry and the gateways' usage records. Every number names its source; nothing here says whether an answer was right (see the evaluations).

## 1. Inventory

7 registrations: 7 active

| Agent or app | Kind | Owner | Team | Risk | Status | Review by |
|---|---|---|---|---|---|---|
| doc-assistant | app | usr-mei | data | low | active | 2027-02-01 |
| helpdesk-assistant | agent | usr-amira | service | medium | active | 2027-01-15 |
| orders-mcp | tool-server | usr-mei | data | high | active | 2026-12-01 |
| release-judge | app | usr-priya | evaluation | medium | active | 2026-10-01 |
| support-mcp | tool-server | usr-kwame | platform | high | active | 2026-12-01 |
| support-workflow | agent | usr-amira | service | high | active | 2026-12-01 |
| ticket-triage | app | usr-amira | service | medium | active | 2027-01-15 |

Found outside the registry (17 findings, `python -m estate discover`):

- 2026-09 azure key az-key-1 chat-small: 5880 requests, US$2.0273: the service team's shared key (owner usr-amira): still used, so not every call passes the gateway
- 2026-09 azure key az-key-1 chat-strong: 769 requests, US$4.4419: the service team's shared key (owner usr-amira): still used, so not every call passes the gateway
- 2026-09 azure key az-key-1 embed-small: 5793 requests, US$0.0084: the service team's shared key (owner usr-amira): still used, so not every call passes the gateway
- 2026-09 azure key az-key-2 chat-small: 324 requests, US$0.0500: the data team's key (owner usr-mei): still used, so not every call passes the gateway
- 2026-09 azure key az-key-3 chat-strong: 202 requests, US$0.8330: a key that nobody told the platform about
- 2026-09 fernway key fw-7Q2K fernway-swift: 1 requests, US$0.0013: a provider without a contract (fernway); a key that nobody told the platform about
- build-runner-3 -> api.fernway.example: 4 connections (3 blocked) from 2026-09-07 to 2026-09-28, key fw-7Q2K: a machine that is not the gateway calls a model provider directly
- docs-01 -> larkfield-ai.openai.azure.example: 324 connections (0 blocked) from 2026-09-01 to 2026-09-09, key az-key-2: a machine that is not the gateway calls a model provider directly
- priya-laptop -> larkfield-ai.openai.azure.example: 204 connections (0 blocked) from 2026-09-03 to 2026-09-10, key az-key-3: a machine that is not the gateway calls a model provider directly
- triage-svc-01 -> larkfield-ai.openai.azure.example: 11673 connections (0 blocked) from 2026-09-01 to 2026-09-08, key az-key-1: a machine that is not the gateway calls a model provider directly
- workflow-01 -> larkfield-ai.openai.azure.example: 776 connections (0 blocked) from 2026-09-01 to 2026-09-10, key az-key-1: a machine that is not the gateway calls a model provider directly
- apps/digest/weekly_digest.py:19: model provider address: http://127.0.0.1:8320/fernway/v1: model provider address in code

Model calls through the gateway this month: 40,754 answered for registered agents.

## 2. Risk tiers

3 high, 3 medium, 1 low (not retired).

- orders-mcp: failure mode fail_closed, kill switch tested: not yet
- support-mcp: failure mode fail_closed, kill switch tested: not yet
- support-workflow: failure mode fail_closed, kill switch tested: not yet

## 3. Spending (US$, from the gateways' records and the dated prices)

| Agent | Team | Calls answered | Refused | Cost | Budget | Used |
|---|---|---|---|---|---|---|
| doc-assistant | data | 873 | 0 | 0.13 | 3.00 | 4% |
| helpdesk-assistant | service | 0 | 0 | 0.00 | 2.00 | 0% |
| orders-mcp | data | 0 | 0 | 0.00 | - | - |
| release-judge | evaluation | 101 | 0 | 0.42 | 8.00 | 5% |
| support-mcp | platform | 0 | 0 | 0.00 | - | - |
| support-workflow | service | 2,589 | 35,182 | 14.28 | 25.00 | 57% |
| ticket-triage | service | 37,191 | 0 | 6.48 | 15.00 | 43% |

| Team | Cost | Budget |
|---|---|---|
| service | 20.76 | 40.00 |
| data | 0.13 | 10.00 |
| evaluation | 0.42 | 10.00 |
| platform | 0.00 | 5.00 |

| Capability | Calls answered | Cost |
|---|---|---|
| strong-reasoning | 2,690 | 14.70 |
| fast-small | 19,618 | 6.58 |
| embed | 18,446 | 0.03 |

| Model that answered | Calls |
|---|---|
| chat-strong (gpt-6.1-sol-2026-09-29) | 2,690 |
| chat-small (gpt-6-luna-2026-09-22) | 19,618 |
| embed-small (text-embedding-3-small) | 18,446 |

## 4. What the controls stopped

| Check | Model calls stopped or failed |
|---|---|
| rate_limit | 28,807 |
| quota | 6,375 |
| route | 40 |
| provider | 15 |

Answers from a fallback: 123. Calls served in fail-open mode: 0. Calls changed by a guardrail: 0.


## 5. Exceptions and incidents

- No exceptions.
- Incident 1 (shadow-ai), 2026-09-15T10:00 to open: the weekly digest sent customer messages to Fernway (no contract) with a personal key; its author left; blocked by the egress rule since 12 September
- Incident 2 (outage), 2026-09-17T10:00 to 2026-09-17T11:30: provider outage (simulated): East US 2 down 1 hour, then both regions 30 minutes
- Incident 3 (runaway), 2026-09-22T14:00 to 2026-09-22T15:00: a bad deployment of the workflow looped (constructed): 837 calls answered, US$4.09; slowed by the rate limit, stopped by the daily token quota

## 6. Reviews and owners

- release-judge: review due on 2026-10-01

## 7. What this evidence cannot answer

- Whether the answers were right: that is each consumer's evaluation (the remap gate) and its reviews.
- What a whole task cost or why it failed: join these records with the app's traces by run ID.
- AI inside bought tools, and AI used outside Larkfield's network: the buying process and asking people.
