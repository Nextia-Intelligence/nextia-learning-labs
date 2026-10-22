# Dataset card: Larkfield's AI estate (the governance course)

Used by: every lesson of [Governing AI Agents: Gateways, Registries and Controls](https://learning.nextia-ai.com/courses/agent-governance/).

| Field | Value |
|---|---|
| What it is | The data and the recorded model traffic of Larkfield's AI estate: the apps that earlier courses built, replayed through this course's gateway. |
| Publisher / creator | Nextia Learning |
| Licence | CC0 1.0 (public domain) for the data. The recorded answers are model outputs that the course team recorded for teaching; they are shared under the same terms. The code is MIT (LICENSE). |
| Made up | Larkfield, Bramble Books, their people, customers, orders and tickets are made up. No real customer wrote any message. Every key is a made-up practice key that only the provider simulator accepts. |

## The files

| File | What one row is | From |
|---|---|---|
| `recordings/answers.jsonl.gz` (in every snapshot: `provsim/recordings/`) | one recorded answer of a real model to one exact request (5,253 answers, 3,953 different requests), with the course and file it comes from, its latency and its time | the agents, evaluation, capstone and LLM applications courses; 269 calls of this course (embeddings of the practice tickets, and one real error); one constructed answer |
| `streams/*.jsonl.gz` (in every snapshot: `apps/streams/`) | one request of an app, exactly as the earlier course sent it, in order | the same recordings |
| `evaluations/*.jsonl.gz` | one item of a consumer's evaluation (a request and what a right answer is) | the evaluation course |
| `data/tickets.jsonl` | one practice ticket (the customer's message, its language and labels) | the MLOps course's practice tickets, made from the evaluation course's cases |
| `data/workflow/` | the support workflow's tasks, practice database and policy passages | the agents course (its own card: `data/workflow/dataset.md`) |
| `data/support/` | the support MCP server's documents, tickets and memberships | the MCP course (its own card: `data/support/dataset.md`) |
| `evidence/*` | the provider bill, the Fernway expense, a summary of the egress log and the estate report of the replayed month | made by the course's month scenario on the real code (the bill and the egress log are the provider simulator's) |

## What is real, what is replayed, what is simulated

- **Real:** every answer of chat-small (gpt-6-luna-2026-09-22), chat-strong (gpt-6.1-sol-2026-09-29), embed-small (text-embedding-3-small) and gemma3:4b, recorded by the earlier courses (Azure AI Foundry, East US 2; gemma3:4b with Ollama on a laptop), and the real HTTP 400 errors that show the models' feature differences.
- **Replayed:** the simulator gives those answers again, for exactly the same requests. It answers no other request ("no recording").
- **Simulated:** the second Azure region (it gives the same recordings), the outages, slow answers and rate limits, the egress log and the egress rule, the bills.
- **Constructed:** the weekly digest script, Fernway (a made-up provider) and its one answer, the runaway loop, the bad configuration change.

## Limitations

- A request that differs by one character from a recorded one gets no answer: lessons that change a prompt or a request see "no recording". The simulator never invents an answer.
- The triage service's answers on chat-strong exist only for the 102 dev cases; the document assistant's only on chat-small.
- The bills use the prices of the course's recordings. Prices change: check the provider's current price page.
