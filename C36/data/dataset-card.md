# Dataset card: the Larkfield inbox (synthetic)

Used by: every lesson of the course *Text Classification and Routing: Send Each Message to the Right Place*, its notebooks and its project `larkroute`.

| Field | Value |
|---|---|
| Source | Made for this course by the Nextia Learning course team (generator kept by the course team) |
| Publisher / creator | Nextia Learning |
| Licence | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (public domain dedication) |
| Attribution text | None needed. "Larkfield inbox, synthetic data from Nextia Learning" is welcome. |
| Version | 1.0 |
| Files used | All files in this folder; their SHA-256 checksums are in `SHA256SUMS` |
| Size | @SIZE@ |

## What one row means

In `messages.csv`, one row is one message that a customer sent to Larkfield, a made-up online shop for home and garden products in Canada, by email, chat or social media, in English or French. The label `route` is the team that must act first (`orders`, `delivery`, `returns_refunds`, `billing`, `product`, `account`) or `needs_person` (a person must read it first). Each message also has a `topic` inside its route, a `priority` (`urgent`, `normal`, `low`), and `routes`: one route, or two routes separated by `|` when the customer asks for two things (the first is the main request).

| File | Rows | What |
|---|---|---|
@FILES@

## How it was made

1. **Structure from fixed seeds.** A program chose, for each message, the time, the channel, the language, the route and topic (from 27 topics with set shares), the priority, the facts (an order number, a product name from Larkfield's catalogue, an amount, a date, a city, a first name) and a short draft from templates. It also planted the situations below.
2. **Natural wording from a language model.** A small hosted model (`gpt-6-luna`) rewrote each draft as the message a customer would send, in the customer's own words, with the channel's style, a tone, a writing style (terse, chatty, upset, a second-language writer, informal Quebec French …), sometimes typos, sometimes a second subject mentioned in passing. Every order number of the draft had to stay in the text; @TEMPLATES@ messages kept the draft text because the rewrite failed this check twice.
3. **Labels.** `route`, `topic` and `priority` are the labels of the generator: the reviewed labels of the course. The rewritten text sometimes makes a message less clear than its label; this is part of real inboxes too.

## Situations we planted on purpose

- A **rare class**: account takeover (@ATO@ messages in the history).
- **Two requests in one message** (about 8%), **sarcasm**, **vague messages** and messages that mention another team's words (a "policy edge").
- **Two labellers**: Chloé and Grace labelled the same 800 training messages (`double_labelled.csv`); they disagree most between `billing` and `returns_refunds`.
- **Noisy labels**: `old_queue.csv` is the queue where each training message ended up in Larkfield's old system; some are wrong, more often for some routes than others.
- **A new product and a strike** in the launch month (2026-02-02 to 2026-03-01): the Grow Hub, a smart watering kit, goes on sale on 2026-02-09 and brings setup questions that the history has no route for; a courier strike from 2026-02-16 to 2026-02-22 raises the late-delivery messages. `launch_month.csv` has no labels; `launch_labels_sample.csv` has Chloé's labels for 250 of its messages, with the new route `devices`.
- **Agents' queue moves** (`corrections.csv`): most are right; quick ones are wrong more often.

The course team keeps the answer key of these situations; it is not in this folder.

## Why synthetic data

Real support messages hold personal data and cannot be shared. A synthetic inbox lets the course plant the problems that real inboxes have (a rare class, people who disagree, noisy labels, a new topic, a real change in the world) and know the answer. The course's case studies use real open datasets.

## Limitations and cautions

- The messages were written by a language model from templates. They are cleaner and more similar to each other than real messages: models score higher here than on a real inbox. Do not quote these accuracies as what to expect elsewhere.
- One small hosted model wrote all the messages. Another LLM can find them easier to read than a person would.
- Product names stay in English in French messages: they are Larkfield's catalogue names.
- The costs in `costs.json` are assumptions for the course, not measured values.
- No real person, order, address or card is in the data. Names are common first names; order numbers and amounts are random.
