# Sources: where every number in this pack comes from

| Numbers | Label | Source |
|---|---|---|
| Evaluation results, judge scores, the five repeated runs, the release rule, the error examples | recorded | [Evaluating and Testing AI Systems](https://learning.nextia-ai.com/courses/evals/): prompt v2 and prompt v3 with the same hosted model (chat-small) on 271 made-up tickets; judge: a stronger hosted model (chat-strong). Labels by the course author, with Grace's written policy. |
| The practice week, "last week", the canary, the shadow test, the release gate | recorded answers in constructed situations | [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/): the same recorded answers replayed in a real ticket service. |
| Tickets a day (base 822) | recorded on a synthetic workload; used as an assumption | [Scaling APIs and AI Workloads](https://learning.nextia-ai.com/courses/scaling/): the average day of its practice ticket workload. |
| Engineering cost per hour (US$40 / US$60 / US$100) | assumption | [AI System Design and Cost Engineering](https://learning.nextia-ai.com/courses/system-design/): its range for people's time. |
| Minutes per reply, adoption, agent cost, error cost, upkeep, one-time hours, the share of bad replies a person misses | assumption | Chosen for this course, each with a low, base and high value ([Review time and cost](3-review-time-and-cost.md)). |
| The value estimate, the sensitivity table, the autonomy ladder | computed | This course's calculation: recorded numbers × assumptions, shown step by step in [Review time and cost](3-review-time-and-cost.md). |

## What a "token" is

Models count text in tokens: pieces of words. On the English documents of the course [AI System Design and Cost Engineering](https://learning.nextia-ai.com/courses/system-design/), one word was 1.48 tokens on average (recorded). The provider charges for tokens in the request and for tokens the model writes, including the tokens of its hidden "thinking". That is why a shorter request can cost more.

## Models change

These numbers are a snapshot of one model on one day. A newer model can be better or worse on the same tickets. The method (the same tickets, the release rule written first, examples read before scores) stays the same.
