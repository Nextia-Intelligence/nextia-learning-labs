# Final assignment: refunds with a new region

Larkfield sends you a new data stream: the refunds per agent, per region and per day, from 2026-01-01 to
2026-03-29. A new region, `west`, goes live in the middle of March. January and February are your reference
months; March is the month you replay with your detection job. We planted some problems in it. Find them,
without an alert flood when the new region goes live.

| File | One row |
|---|---|
| `final_refunds_agents.csv` | one agent on one working day: `date, agent_id, orders, refunds, refund_amount` |
| `final_refunds_regions.csv` | one region on one day: `date, region, orders, refunds, refund_amount` |
| `final_refunds.csv` | one refund: `refund_id, date, agent_id, order_id, region, amount, reason` |

There is no answer key here. The course team checks your work with the evidence that the assignment page asks for.
The data is synthetic and has no real people.
