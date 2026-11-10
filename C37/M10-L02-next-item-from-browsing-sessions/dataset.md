# Dataset card: OTTO Recommender Systems Dataset (a fixed sample)

Used by: the case study *Next item from browsing sessions* in the recommendations course, `C37/M10-L02-next-item-from-browsing-sessions/next-item-from-browsing-sessions.ipynb` (and the solution notebook)

| Field | Value |
|---|---|
| Source | OTTO Recommender Systems Dataset: <https://github.com/otto-de/recsys-dataset> (files on Kaggle: <https://www.kaggle.com/datasets/otto/recsys-dataset>, which needs an account) |
| Publisher / creator | OTTO (Philipp Normann, Sophie Baumeister, Timo Wilm) |
| DOI | [10.34740/KAGGLE/DSV/4991874](https://doi.org/10.34740/KAGGLE/DSV/4991874) |
| Licence | [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). The repository's README says: "The OTTO dataset is released under the CC-BY 4.0 License, while the code is licensed under the MIT License." |
| Attribution text | "OTTO Recommender Systems Dataset" by Philipp Normann, Sophie Baumeister and Timo Wilm (OTTO), <https://github.com/otto-de/recsys-dataset>, licensed under CC BY 4.0. Changed by Nextia Learning: a sample of every 5th session of the test week, one row per event, timestamps in seconds (see *Changes we made*). |
| Citation | Normann, P., Baumeister, S. and Wilm, T. (2023). OTTO Recommender Systems Dataset: A real-world e-commerce dataset for session-based recommender systems research. Kaggle. https://doi.org/10.34740/KAGGLE/DSV/4991874 |
| Version or access date | The test file `otto-recsys-test.jsonl` of the Kaggle dataset `otto/recsys-dataset`, read in November 2026 |
| File used | `otto-sample.csv.gz`, kept next to the notebooks in labs: yes (CC BY 4.0 allows copies with attribution) |
| SHA-256 | `c8d74048524643a0ebf0abd7a3be10792a9895648b21332727990e6588c80a91` |
| Size | 2,763,918 rows × 4 columns, 19.9 MB compressed; 334,361 sessions, 491,129 products |

## What one row means

One event in one visit to the OTTO online shop (web or app) in Germany, from Monday 29 August to Sunday 4 September 2022: a click on a product page, a basket add ("cart") or an order. There is no target column: the case study cuts each visit at a random point and predicts the rest of the visit (the next click, and the products carted and ordered).

## Columns

| Column | Meaning |
|---|---|
| `session` | The visit's ID (anonymised). In OTTO's data, a session is all the activity of one user in the period. |
| `aid` | The product's ID (anonymised; not an article number of otto.de). |
| `ts` | The time of the event, Unix time in whole seconds (UTC). Add 2 hours for German summer time. |
| `type` | `clicks`, `carts` or `orders`. |

## Why this dataset

Real browsing sessions of visitors with no other history, with three kinds of events and timestamps: exactly the cold-start situation of a shop's anonymous visitors, measured on clicks, carts and orders separately. CC BY 4.0 allows a hosted copy. Compared with Retailrocket (CC BY-NC-SA 4.0: not allowed), YOOCHOOSE and Diginetica (no licence found: not allowed), the Coveo SIGIR eCom 2021 data (custom terms: not allowed) and the Tianchi Taobao data (own terms and an account: not allowed). Research notes: `nextia-learning/reference/c37/m10/cs2/DATASET-RESEARCH.md`.

## Changes we made

- **Only the test file** (the week of 29 August to 4 September 2022), not the four training weeks.
- **Only every 5th session:** the sessions whose ID is a multiple of 5. Whole sessions are kept, so no visit is cut by the sampling. The full test file has 1,671,803 sessions and 13,851,293 events; the sample has 334,361 and 2,763,918.
- **One CSV row per event** instead of one JSON line per session (`session,aid,ts,type`), in the source's order (by session, events in time order).
- **Timestamps in whole seconds** instead of milliseconds.
- Compressed with gzip (with a fixed file time, so the checksum repeats). Nothing else was changed. Script: `nextia-learning/reference/c37/m10/cs2/make_sample.py`.

## Traps (the case study deals with each)

- **Times are in UTC.** The shop's days start at 22:00 UTC (midnight in Germany, summer time). The case study counts days from Monday 29 August, 00:00 German time.
- **A visit can start with a cart or an order:** the product was in the basket before the week started, or came from a wish list (OTTO's FAQ).
- **The same product appears many times in one visit:** visitors go back to a product they saw. Count it once per visit where that matters.
- **The last visits are cut by the end of the week** (Sunday 4 September, 23:59 German time).
- **Only about 20% of the product page views came from OTTO's own recommendations** (OTTO's FAQ); most came from search and product lists.

## Limitations and cautions

- One shop, one week in 2022, in Germany. Results say nothing about other shops, other seasons or today's customers.
- A fifth of the test week only. Co-visitation and ALS learn from much less than OTTO's four training weeks, so their numbers here are lower than on the full data.
- No product names, prices or categories: products are numbers only.
- IDs are anonymised. Do not try to identify visitors or products.
