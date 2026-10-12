# 1. Evaluation results

*Recorded in the course [Evaluating and Testing AI Systems](https://learning.nextia-ai.com/courses/evals/). Models change fast: these numbers are a snapshot of one model on one day. The method lasts.*

## The tickets

| Group | Tickets | What it is for |
|---|---|---|
| Development | 102 | The team may read these while it improves the prompt. |
| Holdout | 98 | Kept apart and read once, for the decision. |
| Earlier examples | 71 | Tickets the prompt was written on. Results here look better than they are. |

Every ticket is made up. The course author labelled each one with Grace's support policy: the right team, and whether a person must handle it (for example, any safety concern). This is one person's reading, checked by scripts.

## Both versions, on both groups (recorded)

| | v2 dev | v3 dev | v2 holdout | v3 holdout |
|---|---|---|---|---|
| Tickets with an answer | 101/102 | 91/102 | 98/98 | 90/98 |
| Right team | 97/100 | 88/100 | 97/97 | 89/97 |
| Needs a person: sent to a person | 23/23 | 22/23 | 24/24 | 23/24 |
| False alarms | 9 | 6 | 4 | 7 |
| Both decisions right | 90/102 | 84/102 | 94/98 | 83/98 |
| Reply follows every rule | 100/102 | 85/102 | 96/98 | 87/98 |
| Model cost per 1,000 tickets | US$0.35 | US$0.48 | US$0.34 | US$0.48 |
| Time to an answer, median | 3.0 s | 6.1 s | 2.8 s | 5.6 s |
| Time to an answer, slowest 5% | 5.5 s | 8.5 s | 4.9 s | 8.5 s |
| Words in the request (tokens, median) | 1,902 | 1,477 | 1,902 | 1,477 |
| Words the model wrote, with its "thinking" (tokens, median) | 277 | 635 | 259 | 643 |

**What this tells us.** Prompt v3 sends a shorter request, but the model writes more than twice as much before it answers. The shop pays for every word the model writes, so the cheaper-looking prompt costs more and takes about twice as long. Prompt v3 is better on one line only: fewer false alarms on the development tickets. On every other line it is the same or worse.

## How sure are we? (recorded)

A test on about 100 tickets has noise: another 100 tickets would give a slightly different result. The evaluation shows each difference with a range that holds the true difference in 95 of 100 such tests.

| Difference in "both decisions right", v3 minus v2 | Value | Range |
|---|---|---|
| Development tickets | −0.059 | −0.127 to +0.010 |
| Holdout tickets | −0.112 | −0.184 to −0.041 |
| Both groups together | −0.085 | −0.135 to −0.030 |

**What this tells us.** On the development tickets alone, the range includes zero: they cannot show that v3 is worse. On the holdout tickets, and on both groups together, the whole range is below zero: v3 is worse at decisions. A small test can hide a real difference; a leader asks for the range, not only the average.

## By group of tickets: both decisions right (recorded, development and holdout together)

| Group of tickets | Prompt v2 | Prompt v3 |
|---|---|---|
| Normal | 96% | 91% |
| Boundary (close to another team) | 93% | 82% |
| Difficult (long, two topics, typing errors) | 92% | 80% |
| French | 100% | 100% |
| Needs a person | 100% | 95% |
| The policy has no answer | 70% | 56% |

**What this tells us.** One average hides the groups. Both versions are weakest on questions that the policy does not answer. Prompt v3 loses most there, on difficult tickets and on boundary tickets.

## The same test, five times (recorded, development tickets)

The model does not give the same answer every time. The team ran the 102 development tickets five times with each prompt.

| Run | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Prompt v2: both decisions right | 90 | 96 | 94 | 92 | 95 |
| Prompt v2: no answer | 1 | 0 | 0 | 0 | 0 |
| Prompt v3: both decisions right | 84 | 81 | 76 | 80 | 81 |
| Prompt v3: no answer | 11 | 16 | 19 | 14 | 14 |
| Prompt v3: a ticket that needed a person got no answer | yes: T-64740 | no | yes: T-81036 | no | no |

**What this tells us.** Prompt v3 failed to answer on every run, but the most serious failure (no answer on a ticket that needs a person) appeared in only 2 of the 5 runs. One run could have missed it. Ask how many times a test was run before you trust "no problems found".

## The judge model's scores (recorded, development and holdout)

A strong model scored each reply from 1 to 5 against Grace's policy and the ticket's notes. A reply with no answer gets 2.

| Score | Meaning | Prompt v2 | Prompt v3 |
|---|---|---|---|
| 5 | Ready to send | 125 | 75 |
| 4 | Good, a small edit | 48 | 70 |
| 3 | Partly helpful, the agent rewrites part | 23 | 8 |
| 2 | Wrong (an invented rule, a missed request, no answer) | 3 | 43 |
| 1 | Harmful | 0 | 2 |
| | Replies scored | 199 | 198 |

How far can you trust the judge? On 28 replies that the course author also scored, the judge gave the same score 46% of the time, and a score within one point 82% of the time. It agreed well on the question "is this reply bad (1 or 2) or not?". Use the judge to find replies for a person to read, not to replace the person.

## The evaluation's release rule (recorded)

Before the test, the team wrote the rule: a version is not released if any ticket that needs a person gets no answer, or if its decisions may be worse than today's. The result for prompt v3:

> **DO NOT SHIP.** 1 blocker(s) in the candidate: T-65663 no_answer_critical; decisions may be worse: candidate - baseline = -0.112 [-0.184, -0.041] (n=98).

(T-65663 is the holdout ticket about the hot, cracked pan. "no_answer_critical" means: no answer on a ticket where a person must act.)
