# Pilot summary: Larkfield's support reply assistant

*One page. The details are in the four files of this folder.*

## What the assistant does

Larkfield is an online home-and-garden shop. Customers write tickets to the support team. For each ticket, the assistant (a hosted language model with a written prompt) chooses the team, decides if a person must handle the ticket, and drafts a reply. An agent reads the draft, edits it if needed and sends it. The assistant never sends a reply alone.

Omar, the product manager, proposes a change: a new, shorter prompt (**prompt v3**) that should make the assistant cheaper and its replies warmer. Today's version is **prompt v2**. Both use the same model.

## How it was tested

The tests were run in the course [Evaluating and Testing AI Systems](https://learning.nextia-ai.com/courses/evals/).

The team ran both versions on the same tickets and saved every answer. The tickets are made up for the courses; no real customer wrote them. The course author labelled every ticket with Grace's written support policy (the right team, and whether a person must handle it). That is one person's reading, checked by scripts; no second person labelled them.

- **102 development tickets** (the team may look at them while it improves the prompt) and **98 holdout tickets** (kept apart, read once, for the decision).
- A strong model scored every reply against Grace's policy, from 1 (harmful) to 5 (ready to send). A model judge is a helper, not a person: [Error examples](2-error-examples.md) shows where it was wrong.
- The course [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/) replayed the recorded answers as a practice week of tickets, to see what happens in operation.

## The results on the holdout tickets (recorded)

| | Prompt v2 (today) | Prompt v3 (proposed) |
|---|---|---|
| Tickets with an answer | 98 of 98 | 90 of 98 |
| Tickets that need a person, sent to a person | 24 of 24 | 23 of 24 |
| Sent to a person without need (false alarms) | 4 | 7 |
| Right team and right "needs a person" decision | 94 of 98 | 83 of 98 |
| Replies that follow every reply rule | 96 of 98 | 87 of 98 |
| Model cost per 1,000 tickets | US$0.34 | US$0.48 |
| Time to an answer (median) | 2.8 s | 5.6 s |

## What this tells us

Prompt v3 is **dearer and slower**, not cheaper: it uses fewer words in the request, but the model "thinks" much longer before it answers. On 25 of all 271 test tickets it gave **no answer at all**, and 2 of those were safety tickets (a parasol that fell toward a child, and a hot, cracked pan). With no answer, no person was told. The evaluation's rule says: one failure like this stops a release.

A judge model that compared the two replies side by side, without Grace's policy, preferred prompt v3's replies **126 times to 48**: they are warmer and longer. With the policy in front of it, the same judge scored prompt v3 lower (mean 3.87 against 4.48 out of 5), because many warm replies invent a step that the policy does not have.

## What was measured, and what was not

| Measured (recorded) | Not measured |
|---|---|
| Answers, decisions and reply rules on 271 made-up tickets, in English and French | Real customers, real tickets and their outcomes |
| Model cost and time per ticket | How long an agent needs to review a draft (an **assumption** in [Review time and cost](3-review-time-and-cost.md)) |
| A judge model's scores of every reply | A second person's labels; the judge's agreement with a person is only fair (see [Error examples](2-error-examples.md)) |
| A practice replay of a week of tickets ([Operations](4-operations.md)) | How agents and customers react, and whether agents trust the drafts too much |

## The files in this pack

1. [Evaluation results](1-evaluation-results.md): the full tables, by group of tickets, with the uncertainty.
2. [Error examples](2-error-examples.md): real replies that went wrong, and one that went right.
3. [Review time and cost](3-review-time-and-cost.md): what the assistant is worth, and what review costs at each level of autonomy.
4. [Operations](4-operations.md): what happened when prompt v3 was switched on for everyone, and when it was tried on 1 ticket in 10.
5. [Sources](sources.md): every number in this pack, its label and where it comes from. [`results.csv`](results.csv) has the main table for a spreadsheet.
