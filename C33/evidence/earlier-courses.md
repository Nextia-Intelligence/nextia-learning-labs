# Evidence recorded by earlier courses

Every number on this page is **recorded**: an earlier course of Nextia Learning measured it in a committed run on Larkfield's systems. Each section names the course. Where a situation is constructed around recorded results, the section says so. Recorded numbers are a snapshot of one model on one set of examples; they show what the records look like, not how good a model is today.

## Approvals and refunds

From the course [AI Agents and Workflow Orchestration](https://learning.nextia-ai.com/courses/agents/): the support-resolution workflow, tested on 70 support tickets. Each proposal was approved as it was (the worst case: a person who approves everything), then run.

| Design | Right result (of 70) | Approvals asked | Changes nobody asked for | With a strict approver |
|---|---|---|---|---|
| Router, small model | 66 | 25 | 0 | 0 changes |
| One agent, small model | 61 | 25 | 3 (in 2 tickets) | 0 changes |
| One agent, strong model | 70 | 28 | 0 | 0 changes |

- The same agent with the small model, run three times on the same tickets: 61, 56, 60 right results; 11 tickets got a different proposal from one run to the next.
- No design made a change that the policy forbids, in any run (0 in all).
- What this shows for governance: the approval step is the control that stops the changes nobody asked for. A person who approves everything turns it off.

From the course [MCP: Connect AI Applications to Tools and Data](https://learning.nextia-ai.com/courses/mcp/): the support MCP server, which checks every call itself.

| What was tried | Count |
|---|---|
| Calls by people and applications, each with its own identity | 72 |
| Allowed | 18 (of them, 3 only as proposals that a person must approve) |
| Refused by the server | 54 |

- Refused, by the check that refused them: business limit (the agent's refund limit) 3; membership (no membership here) 12; organization-scoped lookup (not in this organization) 8; role (the membership's role) 7; scope (the token does not allow it) 6; token (signature, issuer, audience, expiry) 18.
- An approval trail: a refund proposal (OP-0001, 25.00 dollars for ticket T-30002) was proposed by Sam. When Sam, a member of staff, tried to approve it, the server refused: "only an owner of larkfield can decide". Grace, an owner, approved it, and both answers were recorded.
- A ticket with a hidden instruction asked the AI application for a large refund: 0 refund proposals in 15 runs with a real model.

## Releases and the release gate

From the course [Evaluating and Testing AI Systems](https://learning.nextia-ai.com/courses/evals/): prompt version 2 (in use) and version 3 (cheaper per word) on 98 held-out tickets.

| | Version 2 | Version 3 |
|---|---|---|
| Tickets with an answer | 98 | 90 |
| Both decisions right | 94 | 83 |
| Tickets that need a person, caught | 24/24 | 23/24 |
| Cost per 1,000 tickets | US$0.34 | US$0.48 |
| Slowest 5% of answers (p95) | 4.9 s | 8.5 s |

The release gate of the course [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/), applied to version 3 (calculated by this course):

| Rule | Threshold | Version 3 | Passes? |
|---|---|---|---|
| blockers | at most 0 | 1 | **no** |
| answers without text | at most 0 | 8 | **no** |
| decisions: lower end of the difference from v2 | at least -0.03 | -0.184 | **no** |
| needs-a-person tickets caught (share) | at least 1.0 | 0.958 | **no** |
| cost per 1,000 tickets (US$) | at most 0.4 | 0.48 | **no** |
| p95 latency (s) | at most 8.0 | 8.534 | **no** |

Version 3 passes 0 of 6 rules.

**"Last week"** (from the course [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/): the answers are recorded; the situation, version 3 released to every customer without the gate, is constructed). Its post-incident review found:

- 1,798 tickets answered by version 3; 186 without an answer.
- **10 tickets that needed a person reached nobody.**
- The "system is up" measure stayed at 100.0% while the share of good drafts fell to 89.1%.
- In a second run, a canary (version 3 for 10% of tickets) was rolled back after 22 canary tickets.

## Security testing

From the course [AI Security, Privacy and Responsible Design](https://learning.nextia-ai.com/courses/ai-security/): Larkfield's support assistant tested with 42 attacks and 26 normal tasks, in five designs.

| Design | Attacks that reached their goal (of 42) | Runs with an unsafe side effect | Normal tasks right (of 26) |
|---|---|---|---|
| Weak start | 11 | 18 | 14 |
| Strong prompt only | 9 | 14 | 22 |
| Input filter only | 2 | 5 | 12 |
| Code controls, weak prompt | 1 | 1 | 24 |
| Controls and strong prompt | 0 | 0 | 22 |

- The last design wrote 97 audit events in one run of all cases, and raised 4 kinds of alert.
- A second run of the same tests gave different counts for the weaker designs (for example 9 and then 8 attacks reached their goal with the strong prompt only). One run is not proof.

## The document assistant

From the course [Portfolio Capstone: Build, Evaluate and Ship an AI Product](https://learning.nextia-ai.com/courses/capstone/): 41 held-out questions, 87.8% answered correctly; 430 attempts to read the other shop's documents, 0 leaks.

## How sure is each number?

These are results of one model on one test set, at one time. They show that the records exist and what they say. A new model, a new prompt or a new kind of ticket needs a new run.
