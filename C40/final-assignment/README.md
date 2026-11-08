# Final assignment: the "complete the look" block

Larkfield added a "complete the look" block to its product pages: a row of products that go with the one on the
page. It wants to know whether the block should stay, and for whom. The course page of the final assignment says
what to deliver.

| File | What it is |
|---|---|
| `data/scenario.json` | What each file is, the test's dates and split, and your targeting budget. |
| `data/test_customers.csv.gz` | The randomised test, one row per customer: the variant, the first visit, the visits, orders, revenue and returns in 28 days, and the spending in the 8 weeks before the test (`pre_spend`). |
| `data/test_visits.csv.gz` | The same test, one row per visit. |
| `data/soft_launch_customers.csv` | The four weeks before the test: customers could turn on a "new look" with the block. Nobody chose at random. |
| `data/next_month_customers.csv` | Next month's customers. Choose whom to show the block to, within the budget. |

The data is synthetic: the course simulator made it, with problems planted on purpose. The true effects are kept
by the course team; your reviewer compares your answers with them.
