# Final assignment: search for Larkfield's new season

This folder is the data of the final assignment of the course *Search and Ranking: Find the Best Match* on
[learning.nextia-ai.com](https://learning.nextia-ai.com/courses/search/final-assignment/). The course page gives
the full task, the steps and the rubric. This file says what is in the folder and how to use it.

## The task in short

Larkfield adds a new season to its catalogue: 2,000 new products that nobody has searched for or clicked yet.
Improve Larkfield's product search for the new season's catalogue, and deliver a search design pack:

1. A test set with judgment guidelines, agreement measured, and a held-out part used once.
2. A baseline (BM25) and at least three other designs from different method families, measured on NDCG@10,
   recall@100, zero-result rate and latency, overall and by slice, with confidence intervals.
3. Query understanding changes, each with the measurement that kept it.
4. A chosen design with its latency and cost per 1,000 queries, and the reason it beats the others for Larkfield.
5. An online test plan (interleaving or A/B) with the metrics, guardrails and stopping rule.

## What is in this folder

| File | Rows | What one row is |
|---|---|---|
| `catalogue_new.csv.gz` | 2,000 | A new-season product, with the same columns as the course's `data/catalogue.csv.gz`. Added between 2026-03-02 and 2026-03-15: no product is in the query log, and none has a click. |
| `queries.csv` | 120 | A query of the new season: `query_id` (N-001 to N-120), `query` and `language` (`en` or `fr`). **No judgments.** |
| `embeddings/products_new.npy` | 2,000 × 384 | The embedding of each new product, in the order of `catalogue_new.csv.gz` (float16, the course's bi-encoder). |
| `embeddings/queries.npy` | 120 × 384 | The embedding of each query, in the order of `queries.csv`. |
| `embeddings/model.json` | | The model and the settings that made the embeddings. |
| `make_data.py` | | Makes a data folder that the `search` command can read: the course data plus this folder plus your judgments. |
| `dataset-card.md` | | Where the data comes from, what is real and what is made by us, and the licence. |
| `SHA256SUMS` | | The checksum of every file. |

The course team keeps the judgments of these queries. They are not here, and you do not need them: **you build
your own judgments for a sample of the queries**, with the course's judging guidelines
(`docs/judging-guidelines.md` in the project). The query IDs are new and in a random order: an ID says nothing
about a query.

## How to use it

Your folder `larkfield-search` is at the end of Module 8, with the course data in `data/`, and
`nextia-learning-labs` is beside it. Check the files, then make the data folder:

```sh
(cd ../nextia-learning-labs/C38/final && shasum -a 256 -c SHA256SUMS | grep -vc ': OK$')   # prints 0
python ../nextia-learning-labs/C38/final/make_data.py
export LARKFIELD_DATA=final-data LARKFIELD_OUTPUTS=outputs-final
search info
search index
```

On Windows (PowerShell):

```powershell
python ..\nextia-learning-labs\C38\final\make_data.py
$env:LARKFIELD_DATA = "final-data"; $env:LARKFIELD_OUTPUTS = "outputs-final"
search info
search index
```

When you have judgments and you have chosen your held-out queries, run `make_data.py` again with
`--judgments` and `--splits` (and `--heldout` once, at the end). `python make_data.py --help` explains each option.
Unset `LARKFIELD_DATA` and `LARKFIELD_OUTPUTS` to go back to the course data.

## Be honest about the data

- The products, the queries and the people's judgments come from WANDS (MIT licence). The prices, stock, sale
  flags and dates are **synthetic**: our code made them. The query log of the course is synthetic too.
- The French queries were **machine-translated** from English queries by a language model. Real French
  customers write differently.
- Some queries are practice problems we made on purpose.
- WANDS is public. Looking up its judgments is not allowed, and it does not help: the rubric grades your method,
  not your score.
