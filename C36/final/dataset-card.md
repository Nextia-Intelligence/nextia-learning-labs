# Dataset card: the Larkfield inbox, final assignment (synthetic)

Used by: the final assignment of the course *Text Classification and Routing: Send Each Message to the Right Place*.

| Field | Value |
|---|---|
| Source | Made for this course by the Nextia Learning course team, with the same generator as `../../data/` |
| Licence | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) |
| Version | 1.0 |
| Files | `data/messages.csv` (1,280 rows), `data/double_labelled.csv` (100), `data/stream.csv` (1,120); SHA-256 in `data/SHA256SUMS` |

## What one row means

As in the course data (`../../data/dataset-card.md`): one message that a customer sent to Larkfield, by email, chat, social media or, new here, through the marketplace where Larkfield also sells. March has labels; April does not.

## Situations we planted on purpose

A new channel (`marketplace`, about 30% of the messages), two new products (the Robot mower R2 from 2026-04-06, with setup questions; the Patio heater), more hard messages (vague, two requests, a policy edge, sarcasm), and the same rare class (account takeover). The course team keeps the answer key of April; it is not in this folder.

## Limitations

The same as the course data: the messages were written by a language model from templates and are easier than a real inbox. The costs are assumptions. No real person, order or card is in the data.
