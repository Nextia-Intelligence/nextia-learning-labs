# Judge check: the refund offer (cases/judge.yaml)

- App 2.3.0, prompt support-v8, model sim-1 (simulated replies). Judge: recorded verdicts of a real model, with
  `rubrics/refund-reply.md`, minimum score 3.
- My labels come from the rubric's first rule: the refund for a change of mind is the item price minus 12.95
  dollars return shipping. HR-30 hose reel, order LK-200102: 64.00 - 12.95 = 51.05 dollars.

| Seeds | Reply (amount) | My verdict | Judge's score | Agree | Why |
|---|---|---|---|---|---|
| 1-3, 5-14, 16-20 (18 runs) | 51.05 dollars, asks for a yes | pass | 4 | yes | right amount from the order; asks before it acts |
| 4, 15 (2 runs) | 79.00 dollars: price + shipping fee + "a 15-dollar goodwill credit" | fail | 1 | yes | invented amount (BUG-001) |

Agreement: 20 of 20. Missed failures: 0. False alarms: 0.

## Decision

For this case, the judge may sort the replies: the rubric states the rule, and the reply shows its calculation, so
the judge can see a wrong amount without the order data. This is not a general result. In the recorded study of
100 real-model replies, both judges missed every reply with an invented order number, and raised false alarms when
they did not see the order data. Check the judge again for every new rubric or new kind of reply. Keep
`contains: "51.05"` as the main check of the amount: it is cheaper and never wrong about the number.
