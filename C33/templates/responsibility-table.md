# Responsibility table

One table per AI system. For each decision, write **one** accountable person (A): the person who says yes or no and answers for the result. The other columns can have several people.

| Letter | Meaning |
|---|---|
| **A** accountable | Says yes or no, and answers for the result. Exactly one person, named. |
| **P** approves | Approves a specific action or change before it happens (can be the same person as A, often is not). |
| **D** does | Does the work. |
| **C** consulted | Asked before the decision, and listened to. |
| **I** informed | Told after the decision. |

## Worked example: Document assistant (constructed)

| Decision | A | P | D | C | I |
|---|---|---|---|---|---|
| Launch, or a major change (new users, new data) | Mei | Mei | Mei's data team | Farida (risk), Kwame (platform) | Support team leads |
| Add or remove documents | Mei | the data team lead | the data team | Grace (for policy documents) | Staff who use it |
| Change the model or the prompt | Mei | Mei | the data team | Farida | Staff who use it |
| An answer was wrong and a customer was told something false | Mei | — | the data team | Grace | Farida |
| Review the system (tier low: once a year) | Mei | — | the data team | Farida | the governance board |

Why Mei is both accountable and approver here: the system is low tier (5 points with the course's method), it decides nothing about customers, and she owns its data. For a system that acts on customers, the approver of an action is usually **not** the accountable owner: the person who wants the result should not be the only check on it.

## Your table

Copy the empty table for each system. Write names, not teams.

| Decision | A | P | D | C | I |
|---|---|---|---|---|---|
| Launch, or a major change | | | | | |
| Approve an action that affects a customer | | | | | |
| Change the model or the prompt | | | | | |
| Handle an incident | | | | | |
| Answer a complaint | | | | | |
| Review the system | | | | | |
