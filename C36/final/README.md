# Final assignment: a new channel and two new products

Larkfield now also sells on an online marketplace, and customers write to it there. Two new products are on sale: the Robot mower R2 (from 2026-04-06) and the Patio heater. You deliver the routing system for the next quarter. The assignment page on the course site lists the evidence to hand in.

| File | One row |
|---|---|
| `data/messages.csv` | one message of March 2026 (1,280), with its labels and a split: `message_id, created_at, channel, language, text, route, topic, priority, routes, split, synthetic` (train 768, validation 256, test 256). The channel `marketplace` is new. The route `devices` (setup questions about smart products) exists since the launch month. |
| `data/double_labelled.csv` | 100 March training messages labelled by two people: `message_id, label_chloe, label_grace` |
| `data/stream.csv` | one message of April 2026 (1,120), with no labels: replay it through your router and write the drift report |

The guidelines, the cost table and the prices are the course's own (`../data/guidelines.md`, `../data/costs.json`, `../data/prices.json`).

There is no answer key here. The course team checks your work with the evidence that the assignment page asks for. The data is synthetic and has no real people.
