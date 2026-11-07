# Dataset card: the Larkfield anomaly data

Used by: every lesson and notebook of the course *Anomaly Detection: Find What Is Unusual*, and the detection job.

| Field | Value |
|---|---|
| Source | Made for this course by Nextia Learning: synthetic data from generators with fixed seeds |
| Publisher / creator | Nextia Learning |
| Licence | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/): you may copy and use it for anything |
| Attribution text | None needed. "Larkfield data, Nextia Learning (synthetic)" is welcome. |
| Version | 1.0 (see `generated.json`: the seeds, the versions and the checksums) |
| Files used | All in this folder |
| SHA-256 | In `SHA256SUMS` (one line per file) |
| Size | About 17 MB in all (the tables below) |

**The data is made up.** Larkfield is the fictional online shop for home and garden products of all our
courses. No row is a real person, a real card or a real payment. The unusual events in it are ones we
**planted** on purpose, so that you can check what a detector finds.

## The tables

| File | One row | Rows | Days |
|---|---|---|---|
| `payments.csv.gz` | one card payment | 343,074 | 2025-06-01 to 2025-11-30 |
| `payments_sample.csv` | the same, four weeks only (fast notebooks) | 50,511 | 2025-08-04 to 2025-08-31 |
| `customers.csv` | one customer | 24,038 | |
| `refunds_daily.csv` | Larkfield on one day: orders, refunds, refund rate | 640 | 2024-04-01 to 2025-12-31 |
| `refunds_agents.csv` | one support agent on one working day | 17,772 | the same |
| `refunds.csv` | one refund | 9,923 | the same |
| `ticket_api_metrics.csv.gz` | one minute of the `ticket-api` service | 86,400 | 2025-09-01 to 2025-10-30 |
| `ticket_api_logs.csv.gz` | one log line of `ticket-api` (a sample) | 137,013 | the same |
| `ticket_api_events.csv` | one release, rollback, restart or configuration change | 22 | the same |
| `orders.csv` | one sales channel on one day | 2,181 | 2024-04-01 to 2026-03-29 |
| `tickets_daily.csv` | one help-desk channel on one day | 2,184 | the same |
| `calendar.csv` | one day, with its holiday | 819 | to 2026-06-28 |
| `sealed-key.txt` | the answer key, packed (see below) | | |

`orders.csv`, `tickets_daily.csv` and `calendar.csv` are the shared Larkfield series: the same numbers as in the
forecasting course. One day, 2025-10-19, has no orders rows: the orders feed dropped it.

### Columns

- **payments**: `payment_id`, `ts` (date and time, shop time), `customer_id`, `account_type` (personal or
  business), `region` (the customer's home region: north, south, coast, and east from 2025-09-01), `amount`
  (always in Canadian dollars), `currency` (the currency of the payment: CAD in Canada, another one abroad),
  `country` (where the card was used), `device_id`, `device_type`, `merchant_category`, `hour`.
- **customers**: `customer_id`, `account_type`, `region`, `first_payment`, `signup`.
- **refunds_daily**: `date`, `orders` (empty on 2025-10-19), `refunds`, `refund_rate`.
- **refunds_agents**: `date`, `agent_id` (A-01 to A-40), `orders` (the orders in the agent's queue), `refunds`,
  `refund_amount`.
- **refunds**: `refund_id`, `date`, `agent_id`, `order_id`, `region`, `amount`, `reason`. A refund of 100 dollars
  or more needs a supervisor's approval.
- **ticket_api_metrics**: `ts` (one minute), `requests`, `error_rate`, `latency_p95_ms`.
- **ticket_api_logs**: `ts`, `level`, `logger`, `message`.
- **ticket_api_events**: `ts`, `kind`, `detail`.

## What we planted (the rules, not the answers)

These kinds of events are in the data. Which rows they are is in the answer key.

- **Payments:** stolen cards used for many small payments in a short time, mostly in a country new for the
  customer; card testing (one device tries many customers' cards with tiny payments); account takeovers (a few
  expensive payments, on a new device or on the customer's own device). And the hook of the first lesson:
  customer C-01234.
- **Refunds:** Larkfield's refund rate rises a little from one day and stays there; one agent refunds far more
  than the others from one day; one agent's refunds cluster just below the 100-dollar approval limit; some
  refunds are paid twice; some daily totals do not match the refunds; the daily feed sends zeros for one day.
- **ticket-api:** a slow memory leak over days; an error spike after a release; a configuration change that
  adds a new log message and moves the latency for good.

**Normal, but unusual** (a detector may flag them; they are not problems): customers who travel, business
customers who place bulk orders, borrowed devices, new phones, Black Friday, the new region `east` (from
2025-09-01), and the Larkfield app (from 2025-10-15, many customers start to pay in the app, on a new device).

## The sealed answer key

`sealed-key.txt` holds the answer key, packed so that you do not read it by accident. The course's
`compare.py` unpacks it to score your detectors. Look at it only when a lesson says so: once you know the
answers, your results no longer say how a detector does on data it has not seen.

## Why synthetic data

Real payment and refund data has real people in it, and nobody publishes the answers. Here every planted event
is known, so every detector can be scored the same way. The case studies of the course use real open data.

## Changes we made

None after generation. The generators are in the course team's repository; the seeds are in `generated.json`.

## Limitations and cautions

- The planted frauds are simpler and more frequent than real fraud: about 1 payment in 70 is planted, far more
  than in a real shop, so that a 50-alert day has enough cases to measure.
- The payments per day (about 1,870) are not the orders per day of the shared series (about 676): the payments
  table is a separate table, at its own scale. Do not compare the two.
- The costs used in the course (a missed fraud, a false alert) are assumptions, not Larkfield's real costs.
