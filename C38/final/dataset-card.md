# Dataset card: Larkfield's new season (final assignment)

Used by: the final assignment of the course *Search and Ranking: Find the Best Match*, with the `larkfield-search`
project at the end of Module 8 and the course data (`../data/`).

| Field | Value |
|---|---|
| Source | Derived from WANDS, the Wayfair ANnotation DataSet: https://github.com/wayfair/WANDS (commit `3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5`) |
| Publisher / creator | Wayfair (WANDS: Chen, Y. et al., *WANDS: Dataset for Product Search Relevance Assessment*, ECIR 2022); the changes and the synthetic parts by the Nextia Learning course team |
| Licence | MIT (the WANDS licence, in the course data's `dataset-card.md`). Our changes and synthetic parts are under the same licence. |
| Attribution text | "Product data and queries derived from WANDS (Wayfair ANnotation DataSet), MIT licence, Copyright (c) 2021 ecir2022." |
| Version or access date | The same WANDS files and checksums as the course data |
| Files here | `catalogue_new.csv.gz`, `queries.csv`, `embeddings/`; the checksum of every file is in `SHA256SUMS` |
| Size | 2,000 products × 17 columns; 120 queries × 3 columns; about 2 MB in all |

## What one row means

- `catalogue_new.csv.gz`: one product of the new season. The columns are the course catalogue's: `product_id`
  (LK- and five digits), `title`, `title_fr`, `product_class`, `category`, `description`, `attributes`, `colour`,
  `style`, `material`, `price`, `on_sale`, `in_stock`, `added`, `rating_count`, `average_rating`, `review_count`.
- `queries.csv`: one query that customers will type in the new season: `query_id`, `query`, `language`.

There is no target column. You make the relevance judgments for the queries you choose.

## Why this dataset

The course data has a log, clicks and judgments for the products that Larkfield already sells. A new season tests
what the course measured on products and queries that the course never used: new products with no clicks, French
queries and practice problems. WANDS has more products and queries than the course published, so the new season
comes from the same shop and the same kind of customer.

## Changes we made

- The 2,000 products are WANDS products of the home and garden departments that the course data does not have.
  We renamed WANDS's house brand to Larkfield, gave each product a new ID and new synthetic fields: `price`,
  `on_sale`, `in_stock` and `added` (from 2026-03-02 to 2026-03-15). About one product in five has a
  machine-translated French title.
- The queries are WANDS queries that the course data does not have, their French versions
  (**machine-translated** by a language model), and practice problems we made on purpose. The IDs are new and
  in a random order.
- The embeddings were computed once with `ibm-granite/granite-embedding-97m-multilingual-r2` (Apache-2.0), the
  bi-encoder of the course, with the settings in `embeddings/model.json`.

## Limitations and cautions

- No product of the new season is in the course's query log (synthetic) and none has a click. Features that come
  from clicks are zero for every new product: this is the cold start of the course.
- The French queries are translations of English queries, so translating them back to English is easier than
  with real French queries.
- The prices, stock, sale flags and dates are synthetic. Do not draw conclusions about real prices from them.
- The course team keeps graded judgments for these queries, by WANDS's annotators. WANDS is public: looking up its
  judgments is not allowed, and it does not help, because the course grades your method, not your score.
