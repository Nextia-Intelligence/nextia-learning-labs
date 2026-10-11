# 4. Operations: what happens after launch

*From the course [MLOps and LLMOps: Operating AI in Production](https://learning.nextia-ai.com/courses/mlops/). The situations are **constructed** practice scenarios on a real service; every answer in them is a **recorded** answer of the real model, sent again (a replay). Time runs faster than in real life, so we count tickets, not days.*

## A normal week with prompt v2 (recorded replay)

| Signal | Value |
|---|---|
| Tickets | 5,754 |
| Sent to a person by the assistant | 1,446 (25.1%) |
| Tickets without an answer | 4 |
| Agents' later reviews that agreed with the assistant | 1,478 of 1,567 (94.3%) |
| Safety tickets that reached a person | 320 of 320 |
| Model cost per 1,000 tickets | US$0.34 |

## "Last week": prompt v3 switched on for every ticket (constructed situation, recorded answers)

Someone changed a setting and prompt v3 answered every ticket. There was no release decision, no gate and no trial on a few tickets first. The evaluation had already said DO NOT SHIP.

| Signal, after the switch | Prompt v2 before | Prompt v3 after |
|---|---|---|
| The service accepted every ticket ("the system is up") | yes | yes: 100.00% |
| Tickets that got a draft | — | 89.1% |
| Tickets without an answer | — | 186 of 1,798 |
| **Tickets that needed a person and reached nobody** | none | **10** |
| Agents' reviews that agreed with the assistant | 93.8% | 83.7% |
| Model cost per 1,000 tickets | US$0.34 | US$0.47 |
| Slowest 5% of answers | 5.2 s | 8.3 s |

**What this tells us.** The usual dashboard ("the system is up, every ticket accepted") stayed green while customers with safety problems waited for nobody. A leader asks for signals about the **outcome** for the customer (did the ticket get a correct answer, did a safety ticket reach a person), not only about the machine.

## The same change done carefully: a canary (constructed situation, recorded answers)

This time prompt v3 answered only 10% of tickets (a "canary"), with an automatic alert on tickets without an answer, and a rule to switch back.

| Signal | Value |
|---|---|
| Canary tickets until the first alarm rule was met | 9 |
| Practice minutes from the start of the canary to the alert | 1.19 |
| Canary tickets until the switch back | 22 |
| Canary tickets without an answer | 3 of 25 |

## A shadow test: nobody sees the new version (constructed situation, recorded answers)

Prompt v3 answered every ticket in the background, and only prompt v2's answers were used.

| Signal | Value |
|---|---|
| Shadow tickets | 543 |
| Shadow tickets without an answer | 42 |
| Customers who saw a prompt v3 answer | 0 |
| Model cost of the shadow per 1,000 tickets (paid on top of the real answers) | US$0.47 |

**What this tells us.** A canary finds the problem after a few customers are touched; a shadow test finds it with none, but you pay for every answer twice while it runs. Both need someone to decide in advance what result stops the change.

## The release gate the team wrote afterwards (recorded)

| Line of the gate | Limit | Prompt v3 |
|---|---|---|
| Tickets that need a person and get no answer | at most 0 | fails (T-65663) |
| Tickets without an answer | at most 0 | fails |
| "Both decisions right" compared with today (lower end of the range) | no more than 3% worse | fails (−0.184) |
| Tickets that need a person, sent to a person | 100% | fails (23 of 24) |
| Model cost per 1,000 tickets | at most US$0.40 | fails (US$0.48) |
| Slowest 5% of answers | at most 8.0 s | fails (8.5 s) |

**What this tells us.** The gate turns "good enough" into lines that anyone can check, before anyone looks at the result. Prompt v3 fails every line. Prompt v2 passes them all, and that is why it may go to a canary.
