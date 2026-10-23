# Usage report: one month

> **Constructed** from recorded unit costs and assumed volumes. The cost of one ticket or one question is **recorded** by an earlier course; the number of tickets and questions in a month is an **assumption**. The unregistered line is **constructed** (a line found on another provider's bill).

## Registered systems

| Agent ID | Requests in 30 days | Unit | Cost of one (recorded) | Where the unit cost comes from | Cost this month | Within its budget? |
|---|---|---|---|---|---|---|
| `triage-service` | 24,660 | tickets | US$0.000341 | MLOps course, practice week, prompt v2 (recorded) | US$8.41 | yes |
| `resolution-workflow` | 1,350 | tickets | US$0.000240 | agents course, router design with the small model (recorded) | US$0.32 | yes |
| `doc-assistant` | 3,600 | questions | US$0.000167 | capstone course, held-out questions (recorded) | US$0.60 | yes |
| `support-mcp` | 2,700 | tool calls | US$0 | it calls no model (MCP course) | US$0.00 | yes |
| **All registered** | | | | | **US$9.33** | |

Volumes (assumptions): 822 tickets a day (the base case of [Leading AI Products and Teams](https://learning.nextia-ai.com/courses/ai-leadership/)); 45 tickets a day for the workflow (the figure of [AI Agents and Workflow Orchestration](https://learning.nextia-ai.com/courses/agents/)); 120 document questions a day (an assumption: nobody measured it); 2 MCP tool calls per workflow ticket.

## Found on another provider's bill

| What | Value |
|---|---|
| Service | An AI service with no Larkfield contract |
| Key owner | a contractor who has left |
| Cost this month | US$63.40 |
| Calls | 4 |
| Customer messages sent | 1,150 |
| Share of all AI spend this month | 87% |

## Coverage

4 of the 8 known AI systems are in the registry (50%). The other 4: the weekly digest script and the 3 AI features inside bought tools.

**What to notice:** the money is small. The risk is not in the bill: it is in what the systems do and where the data goes.
