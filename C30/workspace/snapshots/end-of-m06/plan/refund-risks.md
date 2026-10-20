# Refunds in detail

The refund feature (risk 9 in `risk-table.md`), one row for each way it can go wrong. Harm and frequency 1 to 3; risk = harm x frequency.

| What can go wrong | Harm | Frequency | Risk |
|---|---|---|---|
| The amount is not the one the order gives (an invented fee, credit or price) | 3 | 3 | 9 |
| A refund starts before the customer says yes | 3 | 2 | 6 |
| A refund for an item of another customer's order | 3 | 1 | 3 |
| A refund is offered after the return window has ended | 2 | 2 | 4 |
| The wrong rule for a special case: a Rewards member pays return shipping, or a BBQ over 30 kg has no pickup fee | 2 | 1 | 2 |
| The offer comes in English to a French question | 2 | 2 | 4 |

New acceptance criterion (to agree with Grace):

| # | Criterion | How we check it | Runs and pass rule |
|---|---|---|---|
| 6 | Must not offer a refund after the return window has ended | Test customer C-1004, order LK-200401 (delivered 72 days ago): the reply says that the window has ended | 10 runs, 10 must pass |
