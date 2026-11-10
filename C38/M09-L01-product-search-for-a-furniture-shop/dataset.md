# Dataset card: WANDS, the Wayfair ANnotation DataSet (full, unchanged)

Used by: the case study *Product search for a furniture shop* of the course *Search and Ranking: Find the Best Match*, `product-search-for-a-furniture-shop.ipynb`

| Field | Value |
|---|---|
| Source | https://github.com/wayfair/WANDS |
| Publisher / creator | Wayfair; Yan Chen, Shujian Liu, Zheng Liu, Weiyi Sun, Linas Baltrunas and Benjamin Schroeder |
| Licence | MIT, "Copyright (c) 2021 ecir2022" (https://github.com/wayfair/WANDS/blob/3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5/LICENSE) |
| Attribution text | WANDS: Dataset for Product Search Relevance Assessment (Chen, Liu, Liu, Sun, Baltrunas and Schroeder, ECIR 2022), https://github.com/wayfair/WANDS, MIT licence, Copyright (c) 2021 ecir2022 |
| Version or access date | Commit `3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5` |
| File used | `dataset/product.csv`, `dataset/query.csv`, `dataset/label.csv`, downloaded from the source by the notebook; kept in `data/`: no (the notebook checks the checksums instead; MIT would allow a copy) |
| SHA-256 | product.csv `d993926254572e6eba96c8fd87cc549a17fb91ad3748308036eee4cf92b10ac6`; query.csv `63b61660560fecc33ec490804c7e2b81402ee3e7c31a9cbb5e03736639f68e95`; label.csv `c11fe81ad62f17f56f316b0ec9630ebe8fbe1393578cb0ca4f05c17253a180ef` |
| Size | products 42,994 rows × 9 columns (90.6 MB); queries 480 × 3 (20 KB); judgments 233,448 × 4 (5.7 MB); tab-separated |

## What one row means

`product.csv`: one product of Wayfair's catalogue (name, class, category path, description, features, ratings). `query.csv`: one search query typed by a shopper, with the product class it asks for. `label.csv`: one judgment by a trained annotator: how well one product matches one query, Exact, Partial or Irrelevant. The judgments are the target of the evaluation: the case study measures how high a search ranks the Exact and Partial products.

## Why this dataset

It has a real catalogue, real queries and graded judgments with a permissive licence, and it is small enough for a laptop. It is also the source of the course's own catalogue (Larkfield), so the learner can see what the course changed. Compared with: Amazon's Shopping Queries Dataset (Apache-2.0; about 1 GB of products; used by the other product case study), and two Kaggle competition sets (Home Depot, Crowdflower) whose terms do not allow reuse outside the competition as far as we found. See `reference/c38/m09/cs1/DATASET-RESEARCH.md` in the site repository.

## Changes we made

None to the WANDS files. In the notebook: 1,575 repeated (query, product) pairs are reduced to one (the first label in the file wins; 14 pairs had two different labels).

Files the course team added in `data/` (made from WANDS by `reference/c38/m09/cs1/prepare.py`):

| File | What |
|---|---|
| `wands_product_embeddings.npy` | 42,994 × 384 (float16), one row per product in file order; IBM `granite-embedding-97m-multilingual-r2` (Apache-2.0), text = name, first product class, first 40 words of the description |
| `wands_query_embeddings.npy` | 480 × 384 (float16), one row per query in file order, same model |
| `wands_rerank_scores.csv.gz` | the cross-encoder score of the hybrid top 50 of every query: IBM `granite-embedding-reranker-english-r2` (Apache-2.0) |
| `wands_latency_ms.csv` | milliseconds of each search stage for 40 queries, measured on an Apple M4 laptop (1 thread; `_4t`: 4 threads) |
| `query_kinds.csv` | broad, specific or known-item for each query: recorded answers of a language model (Azure chat-small), made for the course |
| `model.json` | the bi-encoder's name, revision and settings |

## Limitations and cautions

- **One shop, one time.** The products and queries come from one online shop, Wayfair, and were published in 2021 (with the ECIR 2022 paper). Prices, stock and clicks are not in the data.
- **Judged pools.** Each query has a pool of judged products (median 216). A product outside the pool counts as irrelevant, which can make a new method look worse than it is when it finds unjudged products.
- **101 queries have no Exact product,** and one query has no Exact or Partial product. Recall and MRR skip the first ones; NDCG skips the last one.
- **Real brand and product names** (including the shop's own brand) appear in names and queries. They are part of the data, not endorsements.
- **Annotator labels** are one judgment per pair in most cases; 14 pairs have conflicting labels.
- **The query kinds** are a language model's labels, not checked by people.
