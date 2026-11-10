# Final assignment: the "complete the look" block

Larkfield added a "complete the look" block to its product pages: a row of products that go with the one on the
page. It wants to know whether the block should stay, and for whom. The course page of the final assignment says
what to deliver and how it is reviewed.

| File | Rows | What one row is |
|---|---|---|
| `data/scenario.json` | | What the files are: the test's dates (28 days from 3 November 2025) and split (50/50 by customer), and your targeting budget (15,000 customers). |
| `data/test_customers.csv.gz` | 93,463 | A customer in the randomised test: the variant (A without the block, B with it), the first visit, and the visits, orders, revenue and returns in the test. Also the customer's province, device, new or returning, tenure, and the orders and spending in the 8 weeks before the test (`pre_orders`, `pre_spend`). |
| `data/test_visits.csv.gz` | 337,741 | A visit in the same test: the date, the customer, the variant, and whether the visit had an order (`ordered`), its revenue and a return. |
| `data/soft_launch_customers.csv` | 40,000 | A customer in the four weeks before the test (6 October to 2 November 2025). Customers could turn on a "new look" with the block (`turned_on_new_look`). Nobody chose at random. Also the visits, the pages viewed and the revenue in those four weeks. |
| `data/next_month_customers.csv` | 50,000 | A customer of next month, with the same columns as before a test. Choose at most 15,000 of them to show the block to. |
| `data/SHA256SUMS` | | The checksum of each file. |
| `make_runs.py` | | Checks the files and writes two runs that the `xp` commands can read: `runs/final-test` and `runs/final-soft`. |

Run `make_runs.py` in your `larkfield-experiments` folder (the snapshot `end-of-m08`), with its virtual
environment active, **after** you write your test plan:

```sh
python ../nextia-learning-labs/C40/final-assignment/make_runs.py --primary revenue --guardrails return_rate
```

Windows (PowerShell): the same command with `..\nextia-learning-labs\C40\final-assignment\make_runs.py`.

`--primary` and `--guardrails` come from your plan: `xp report` uses them. `runs/final-test` adds one column to the
customers, `segment` (device and new or returning, for example `mobile-new`), for `xp analyse --by segment`. In
`runs/final-soft`, the column `used_block` is a copy of `turned_on_new_look`: `xp adjust` and `xp refute` read that
name.

The data is synthetic: the course simulator made it, with problems planted on purpose. There are no real people.
The true effects are kept by the course team, so `xp check` cannot help you here. Your reviewer compares your
answers with them.
