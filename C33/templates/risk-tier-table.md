# Risk tiers and the controls they need

> **The course's method**, constructed for this course. It is not a law or a standard. A law may put a use in a category of its own (for example "high-risk" under the EU AI Act): the two questions before scoring send those uses to a specialist first.

## Before you score

- Is it a use that a law bans or calls high-risk (for example hiring, credit, insurance prices, education, essential public services)?
- Does it make a decision about a person based only on automated processing?

If the answer to either question is yes, ask the legal specialist before you go on, whatever the score.

## Score four factors, from 1 to 3

### Harm of a wrong result

1. Small and easy to undo (a wrong summary, a slower answer)
2. Money or time lost, and it can be corrected (a wrong refund, a wrong amount)
3. Safety, legal rights or access to a service, or hard to undo

### People affected

1. Only Larkfield staff
2. Customers, suppliers or other people outside Larkfield
3. Vulnerable people, or a decision about a person's access to a service, a job, credit or insurance

### Autonomy

1. Suggests or summarises; a person decides
2. Proposes an action; a person approves each one
3. Acts alone

### Data

1. No personal data
2. Personal data (names, messages, order numbers)
3. Sensitive personal data (health, money accounts, children), or data sent to a company with no contract

## Add the four scores

| Sum | Tier |
|---|---|
| 4 to 6 | low |
| 7 to 8 | medium |
| 9 to 12 | high |

Two rules change the result:

1. A harm of 3 is never low: the tier is at least medium.
2. A system that acts alone (autonomy 3) with a harm of 2 or more is high.

## The controls of each tier

Each tier keeps the controls of the tiers below it.

| Tier | Controls |
|---|---|
| low | Listed in the inventory with a named accountable owner<br>Acceptable-use rules apply<br>Fast path: the owner and the risk lead decide within 2 working days<br>Review once a year |
| medium | everything in low, and:<br>A system card, kept current<br>A vendor check before buying or switching on<br>An evaluation before each release, with the result in a decision record<br>A person approves every action that affects a customer<br>A change log<br>Review every 6 months |
| high | everything in low and medium, and:<br>An impact assessment, signed by the accountable owner and reviewed by the board<br>A release gate with written thresholds<br>Monitoring with pause conditions, and an incident plan<br>A privacy or legal review where personal data or the law is involved<br>Review every 3 months |

## Worked example: Document assistant

Harm 1 (a wrong answer to a member of staff, who can check the cited document) + people 1 (staff only) + autonomy 1 (it answers; a person decides) + data 2 (staff-only documents) = **5: tier low**. Controls: the 4 of the low tier. Next review: in 12 months.

## Your table

| System | Harm | People | Autonomy | Data | Sum | Rule used | Tier | Controls it needs that it does not have yet |
|---|---|---|---|---|---|---|---|---|
| S1 Ticket triage service | | | | | | | | |
| S2 Support-resolution workflow | | | | | | | | |
| S3 Document assistant | | | | | | | | |
| S4 Support MCP server | | | | | | | | |
| S5 Weekly digest script | | | | | | | | |
| S6 Reply suggester in the helpdesk tool | | | | | | | | |
| S7 Meeting-notes tool | | | | | | | | |
| S8 Invoice reader in the accounting tool | | | | | | | | |
