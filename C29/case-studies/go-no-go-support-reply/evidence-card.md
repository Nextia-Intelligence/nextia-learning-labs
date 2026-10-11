# Evidence card: go/no-go for the support reply assistant

*Every number you may use in this case study, its label and its source. If a number is not on this card, it is not evidence for this decision.*

## Recorded (measured in an earlier course's runs)

| Number | Value | Source |
|---|---|---|
| Test tickets: development / holdout | 102 / 98 | [Evaluating and Testing AI Systems](https://learning.nextia-ai.com/courses/evals/) |
| Holdout tickets with an answer, v2 / v3 | 98 / 90 of 98 | same |
| Holdout tickets that need a person, sent to a person, v2 / v3 | 24/24 / 23/24 | same |
| Holdout "both decisions right", v2 / v3 | 94 / 83 of 98 | same |
| Difference v3 − v2 on the holdout, with its 95% range | −0.112 (−0.184 to −0.041) | same |
| Tickets with no answer, all 271 test tickets, v2 / v3 | 1 / 25 | same |
| Model cost per 1,000 holdout tickets, v2 / v3 | US$0.34 / US$0.48 | same |
| Median time to an answer, holdout, v2 / v3 | 2.8 s / 5.6 s | same |
| Request size (tokens, median), v2 / v3 | 1,902 / 1,477 | same |
| Side-by-side judge **without** the policy: v3 preferred / v2 preferred | 126 / 48 (the order of the two replies changed the verdict on 25 of 200 tickets) | same |
| Judge **with** the policy: mean score v2 / v3 (out of 5) | 4.48 / 3.87 | same |
| Judge agreement with the course author's scores (same score / within one point) | 46% / 82% of 28 | same |
| Five repeated runs: runs where v3 left a ticket that needs a person without an answer | 2 of 5 | same |
| Practice week: share of tickets sent to a person | 25.1% | [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/) (recorded answers, replayed) |
| "Last week" (v3 for everyone): tickets that needed a person and reached nobody | 10 | same (constructed situation, recorded answers) |
| Canary (v3 on 10% of tickets): canary tickets until the switch back | 22 | same |

## Assumptions (chosen for the course; each has a range)

| Assumption | Low / base / high | Where it is used |
|---|---|---|
| Minutes to write a reply by hand | 4 / 6 / 8 | value estimate, autonomy ladder |
| Minutes to review a usable draft | 2.5 / 1.5 / 1 | same |
| Minutes to approve or reject (no editing) | 1.0 / 0.6 / 0.4 | autonomy ladder |
| Share of bad replies a person lets through: editing a draft / only approving | 20% / 10% / 5% / 50% / 30% / 20% | autonomy ladder |
| Agent cost per hour | US$25 / US$32 / US$40 | both |
| Tickets a day | 600 / 822 / 1,100 | value estimate |
| Adoption | 40% / 70% / 90% | value estimate |

## Computed (recorded numbers × assumptions; shown step by step in [Review time and cost](../../evidence/pilot-evidence-pack/3-review-time-and-cost.md))

| Number | Value |
|---|---|
| Net value a year of today's assistant (v2), low / base / high | −US$52,905 / US$287,661 / US$1,069,007 |
| People cost per 1,000 drafted tickets at the draft level, v2 / v3 (base) | US$1,253 / US$1,728 |
| People cost per 1,000 at the approve level, v2 / v3 (base) | US$613 / US$920 |
| Wrong or harmful replies reaching customers per 1,000: v2 draft / v2 approve (base) | 1.5 / 4.5 |

## Constructed

Omar's proposal and its wording; Nadia and her Friday deadline; the "last week" and canary situations (their answers are recorded).

## Known gaps (say them in your memo)

- No real customer, ticket or agent was measured. The tickets are made up.
- How long agents take to review or approve a draft was **not measured**: it is the assumption that changes the value most.
- One person (the course author) labelled the right answers; no second person did.
- The judge model agrees with a person only fairly on the exact score; it is better at "bad or not".
- Nobody measured whether agents trust the drafts too much (approve without reading).
- The holdout set has 98 tickets: rare problems (a harmful reply in 1 of 500) can hide in a set this size.
