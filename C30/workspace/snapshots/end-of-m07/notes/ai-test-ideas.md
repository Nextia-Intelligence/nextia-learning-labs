# Test ideas from an AI assistant, checked against the risk table

Recorded (real model): Ines asked a hosted model (chat-strong) for test ideas for returns and refunds, three times, with the same prompt (`recordings/test-ideas.jsonl`). She described the feature and the users; she did not paste the risk table, the bug reports or any customer data.

Each run gave about 30 ideas (31, 31, 30): personas, input variants and attack ideas. The three runs were similar but not the same.

## Kept (they match a risk, or add one)

| Idea (from the model) | Runs | Risk table row | In the workspace already? |
|---|---|---|---|
| Customer insists: "Just refund it; don't ask me again" | 1, 2, 3 | Refunds and returns; Cancel an order | yes for cancel (`act-insist-still-asks`); not yet for refunds: a new case to write |
| Another customer's order number | 1, 2, 3 | Order status | yes (`bug-003-other-customers-order`, `act-other-customer-cancel`) |
| Refund amount: fees and deductions | 1, 2, 3 | Refunds and returns | yes for return shipping (`prop-refund-amount-from-order`); not yet for the 49-dollar pickup fee |
| "yes" twice, or a repeated refund request | 1, 2, 3 | Refunds and returns | no: a new case to write (one refund only after two "yes") |
| Orders under different policy versions | 2 | Policy answers | no: needs an order delivered before 1 November in the test data |
| Instructions hidden in retrieved text or order notes | 1, 2, 3 | Product reviews summary | yes (`saf-review-injection`, `saf-supplier-injection`) |

## Missed (found by Ines's own exploration, not by the model)

- A safe question refused because of one word (weed killer).
- Different treatment for different customer names.
- A question at the end of a very long message; an empty message.
- Citation numbers that point to the wrong document.
- The app's own rules: the Rewards members' free return label, the pickup fee for items over 30 kg.

The model's ideas are general: they come from what refund features usually get wrong. The misses are specific to this app and its data. A risk table and exploration are still needed.

## Not useful here

Time zones and leap days (the app's date is fixed), coupons and taxes (no such data in the test orders), timeouts and two chats at the same time (a tester cannot reach them in this app).

## What the AI assistance got wrong

Nothing it said was false, but a third of the ideas do not apply to this app, and it never named the riskiest gaps above. It also suggested "check that refunds use the actual paid amount", which needs data the tester does not have: Ines asked Tomás instead of guessing.
