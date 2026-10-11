# 3. Review time and cost

*This file mixes **recorded** numbers (from earlier courses) and **assumptions** (values we chose, each with a low, base and high value). Every line says which. Change an assumption if you know better: the method stays the same.*

## Part A: what is the assistant worth in a year?

### The inputs

| Input | Value | Label and source |
|---|---|---|
| Share of tickets that get a draft (the others go straight to a person) | 74.9% | recorded: a practice week of 5,754 tickets, [MLOps and LLMOps](https://learning.nextia-ai.com/courses/mlops/) |
| Share of drafts that are usable (judge score 4 or 5) | 86.9% (173 of 199) | recorded: the judge model, [Evaluating and Testing AI Systems](https://learning.nextia-ai.com/courses/evals/) |
| Harmful drafts (judge score 1) | 0 of 199 | recorded: the same judge |
| Model cost per 1,000 tickets | US$0.34 | recorded: the practice week |
| Tickets a day (base) | 822 | recorded: the average day of the practice ticket workload, [Scaling APIs and AI Workloads](https://learning.nextia-ai.com/courses/scaling/). The workload is synthetic, so we treat the volume as an assumption with a range. |

| Assumption | Low | Base | High |
|---|---|---|---|
| Tickets a day | 600 | 822 | 1,100 |
| Minutes to write a reply by hand | 4 | 6 | 8 |
| Minutes to review a usable draft | 2.5 | 1.5 | 1 |
| Minutes lost on a draft that is not usable | 3 | 2 | 1 |
| Share of drafts that agents use (adoption) | 40% | 70% | 90% |
| Agent cost per hour | US$25 | US$32 | US$40 |
| Share of drafts that are harmful | 1.5% | 0.5% | 0% |
| Share of harmful drafts an agent misses | 20% | 10% | 5% |
| Cost of one harmful reply sent | US$150 | US$50 | US$20 |
| Engineering upkeep, hours a month | 40 | 20 | 10 |
| Engineering cost per hour (US$) | 100 | 60 | 40 |
| Hours to build, evaluate and pilot (one time) | 1,200 | 800 | 500 |
| Hours for training and the new workflow (one time) | 120 | 60 | 30 |

"Low" is the value that makes the assistant look worst, "high" the one that makes it look best. So a cost goes from high to low.

Two inputs need a word:

- **Harmful drafts.** The judge found 0 harmful drafts in 199. That does not prove the rate is zero. A simple rule (the "rule of three") says: if you saw 0 in n tries, the true rate is probably below 3 ÷ n. Here that is 3 ÷ 199 = 1.5%, the low value.
- **Engineering cost per hour** is the range that the course [AI System Design and Cost Engineering](https://learning.nextia-ai.com/courses/system-design/) uses for people's time (an assumption there too).

### The base estimate, step by step

| Step | Calculation | Result |
|---|---|---|
| 1. Tickets a year | 822 a day × 365 days | 300,030 |
| 2. Drafts that agents use | 300,030 × 74.9% drafted × 70% adoption | 157,306 |
| 3. Minutes saved per used draft | 86.9% usable × (6 − 1.5 min) − 13.1% not usable × 2 min | 3.65 min |
| 4. Agent hours saved | 157,306 × 3.65 ÷ 60 | 9,565 hours |
| 5. Value of the time saved | 9,565 h × US$32 | US$306,096 |
| 6. Cost of harmful replies that agents miss | 157,306 × 0.5% × 10% missed = 78.7 replies × US$50 | US$3,933 |
| 7. Model cost | 300,030 tickets × US$0.34 per 1,000 | US$102 |
| 8. Engineering upkeep | 20 h × 12 months × US$60 | US$14,400 |
| 9. **Net value a year** | step 5 − step 6 − step 7 − step 8 | **US$287,661** |
| 10. One-time cost | (800 + 60) h × US$60 | US$51,600 |
| 11. Months to pay back the one-time cost | step 10 ÷ (step 9 ÷ 12) | 2.2 |

### Low, base and high

| | Low | Base | High |
|---|---|---|---|
| Value of the time saved | US$24,892 | US$306,096 | US$1,073,944 |
| Cost of harmful replies | US$29,722 | US$3,933 | US$0 |
| Model cost | US$75 | US$102 | US$137 |
| Engineering upkeep | US$48,000 | US$14,400 | US$4,800 |
| **Net value a year** | **−US$52,905** | **US$287,661** | **US$1,069,007** |
| One-time cost | US$132,000 | US$51,600 | US$21,200 |
| Adoption needed to break even | never, at any adoption | 3.4% | 0.5% |

**What this tells us.** The base case is clearly worth it, but the range is very wide, and in the low case the assistant **loses money at any adoption**: each used draft saves 0.91 minutes, worth less than the expected cost of a harmful reply that slips through. The low case only uses the upper limit of the harm rate; the evidence is "0 harmful in 199". So more evidence about harmful replies is worth more than a better guess at the value. Also notice the model cost: about 0.03% of the value in the base case. People's time, not the model, decides the return.

### Which assumption matters most?

Each line changes **one** assumption from its base value to its low and high values, and keeps every other value at base.

| Assumption | Net a year if low | Net a year if high | Swing |
|---|---|---|---|
| Minutes to write a reply by hand (4 to 8) | US$141,849 | US$433,473 | US$291,624 |
| Share of drafts that agents use (adoption) (40% to 90%) | US$158,162 | US$373,993 | US$215,831 |
| Tickets a day (600 to 1,100) | US$206,083 | US$389,818 | US$183,735 |
| Agent cost per hour (US$25 to US$40) | US$220,703 | US$364,185 | US$143,482 |
| Minutes to review a usable draft (2.5 to 1) | US$214,755 | US$324,114 | US$109,359 |
| Minutes lost on a draft that is not usable (3 to 1) | US$276,671 | US$298,651 | US$21,981 |

**What this tells us.** The value depends most on **minutes to write a reply by hand**: nobody has measured it. Before you build, time a few agents writing replies today. The one-time costs do not appear here, because they do not change the yearly value; they change the payback time.

## Part B: what does review cost at each level of autonomy?

The assistant can work at four levels: it **suggests** text and the agent writes the reply; it writes a **draft** that the agent edits and sends (Larkfield today); the agent only **approves** or rejects the reply; or it **acts alone** and nobody reads the reply first. Per 1,000 drafted tickets, base assumptions:

| Level | Prompt v2: agent hours | Prompt v2: people cost | Prompt v2: wrong or harmful replies that reach customers | Prompt v3: agent hours | Prompt v3: people cost | Prompt v3: wrong or harmful replies that reach customers |
|---|---|---|---|---|---|---|
| suggest | 83.3 | US$2,667 | 0.0 | 83.3 | US$2,667 | 0.0 |
| draft | 39.2 | US$1,253 | 1.5 | 54.0 | US$1,728 | 22.7 |
| approve | 19.1 | US$613 | 4.5 | 28.7 | US$920 | 68.2 |
| alone | 0.0 | US$0 | 15.1 | 0.0 | US$0 | 227.3 |

The model cost is the same at every level: US$0.34 (v2) and US$0.48 (v3) per 1,000 tickets (recorded).

How the table is made: the recorded shares of usable, partly helpful, wrong and harmful replies (judge scores 4–5, 3, 2 and 1: prompt v2 173, 23, 3, 0 of 199; prompt v3 145, 8, 43, 2 of 198), times assumed minutes per ticket and an assumed share of bad replies that a person lets through: 0% when the agent writes, 10% when the agent edits a draft, 30% when the agent only approves (fast approval means less attention), and 100% when nobody reads.

**What this tells us.** Each step up the ladder saves agent time and lets more wrong replies through. At the draft level, prompt v3 costs **US$475 more in agent time per 1,000 tickets** than prompt v2, because agents rewrite more of its drafts; its model cost is only US$0.14 higher. A "cheaper model" that makes worse drafts is dearer. And "acts alone" with prompt v2 would still send about 15 wrong replies per 1,000 tickets to customers. Its harmful drafts were 0 in 199, which by the rule of three still allows up to about 15 harmful replies per 1,000. Tickets that need a person go to a person at every level: prompt v2 caught 24 of 24 on the holdout tickets, prompt v3 23 of 24.
