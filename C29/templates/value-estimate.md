# Value estimate

*Module 1, lesson 3. Copy this page or use [`value-estimate.csv`](value-estimate.csv) in a spreadsheet. The worked example for Larkfield's support reply assistant is in [Review time and cost](../evidence/pilot-evidence-pack/3-review-time-and-cost.md).*

**Use case:**
**Unit of work** (one ticket, one invoice, one call …):

## 1. Inputs

Write every input with a low, base and high value and its label: **recorded** (measured, with the source), **price** (with the page), **assumption** (your choice; say why), or **constructed**. "Low" is the value that makes the use case look worst.

| Input | Low | Base | High | Label | Source or reason |
|---|---|---|---|---|---|
| Units a year | | | | | |
| Share of units the AI can handle (the others go to a person) | | | | | |
| Share of AI outputs that are usable | | | | | |
| Adoption: share of units where people use the output | | | | | |
| Minutes per unit today (without AI) | | | | | |
| Minutes per unit to review a usable output | | | | | |
| Minutes lost on an output that is not usable | | | | | |
| Cost of one hour of the people who do the work | | | | | |
| Share of outputs that cause harm, and share that review misses | | | | | |
| Cost of one harmful output that reaches a customer | | | | | |
| AI cost per unit (model, service) | | | | | |
| Upkeep: hours a month and cost per hour | | | | | |
| One-time cost: build, pilot, training | | | | | |

## 2. The calculation (write every step with its numbers)

1. Units used = units a year × share the AI handles × adoption
2. Minutes saved per used unit = usable share × (minutes today − minutes to review) − not-usable share × minutes lost
3. Value of time saved = units used × minutes saved ÷ 60 × cost per hour
4. Cost of harm = units used × harmful share × missed share × cost per harmful output
5. Running cost = AI cost per unit × units a year + upkeep a year
6. **Net value a year** = step 3 − step 4 − step 5
7. Payback in months = one-time cost ÷ (net value a year ÷ 12)

| | Low | Base | High |
|---|---|---|---|
| Value of time saved | | | |
| Cost of harm | | | |
| Running cost | | | |
| **Net value a year** | | | |
| One-time cost | | | |
| Payback (months) | | | |

## 3. Which assumption matters most?

Change one input at a time from base to low and to high, and keep the others at base. Write the input with the biggest swing first.

| Input | Net value if low | Net value if high | Swing |
|---|---|---|---|
| | | | |
| | | | |
| | | | |

## 4. What this tells us

- The range in one sentence:
- The assumption that changes the result most, and how we will measure it before we build:
- Is the AI cost a large or a small part of the result?
