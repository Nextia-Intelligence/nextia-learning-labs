# Dataset card: the Larkfield search data

Used by: the course *Search and Ranking: Find the Best Match* (every module), the `larkfield-search` project and the notebooks.

| Field | Value |
|---|---|
| Source | Derived from WANDS, the Wayfair ANnotation DataSet: https://github.com/wayfair/WANDS (commit `3b74dcf4ba29ab8ff3e6a50b5b09fc627cb882b5`) |
| Publisher / creator | Wayfair (WANDS: Chen, Y. et al., *WANDS: Dataset for Product Search Relevance Assessment*, ECIR 2022); the changes and the synthetic parts by the Nextia Learning course team |
| Licence | MIT (the WANDS licence, below). Our changes and synthetic parts are under the same licence. |
| Attribution text | "Product data, queries and judgments derived from WANDS (Wayfair ANnotation DataSet), MIT licence, Copyright (c) 2021 ecir2022." |
| Files from WANDS | `product.csv` SHA-256 `d993926254572e6eba96c8fd87cc549a17fb91ad3748308036eee4cf92b10ac6`, `query.csv` `63b61660560fecc33ec490804c7e2b81402ee3e7c31a9cbb5e03736639f68e95`, `label.csv` `c11fe81ad62f17f56f316b0ec9630ebe8fbe1393578cb0ca4f05c17253a180ef` |
| Files here | the checksum of every file is in `SHA256SUMS` |

## The files

| File | One row is | Real or made by us |
|---|---|---|
| `catalogue.csv.gz` | a product: `product_id` (LK- and five digits), `title`, `title_fr`, `product_class`, `category`, `description`, `attributes`, `colour`, `style`, `material`, `price`, `on_sale`, `in_stock`, `added`, `rating_count`, `average_rating`, `review_count` | titles, classes, categories, descriptions, attributes and ratings: real (WANDS). `title_fr`: machine-translated for a part of the catalogue. `price`, `on_sale`, `in_stock`, `added`: **synthetic** |
| `queries.csv` | a query with judgments: `query_id`, `query`, `language`, `split` (train, validation, test), `source`, `base_query_id`, `query_class`, `qtype`, `band`, `has_number`, `planted`, `log_searches` | see "The queries" below |
| `judgments.csv.gz` | a graded judgment: `query_id`, `product_id`, `grade` (2 exact, 1 partial, 0 irrelevant) | real (WANDS annotators), copied to the French and misspelt versions of a query; rule-based for the planted queries |
| `log/searches.csv.gz` | one search of the query log: `search_id`, `session_id`, `date`, `time`, `query`, `query_id`, `results`, `clicks`, `added_to_cart`, `reformulated` | **synthetic** |
| `log/impressions.csv.gz` | one product shown in a search: `search_id`, `position`, `product_id`, `clicked`, `added_to_cart` | **synthetic** |
| `synonyms.csv` | a synonym rule | written by the course team (one rule, "light, lamp", is a practice problem we made on purpose) |
| `costs.json` | a cost or price that the lessons use | assumptions |
| `embeddings/` | `products.npy` (one row per product, catalogue order), `queries.npy` (one row per query, `queries.csv` order), `model.json` | computed once by the course team with the bi-encoder below |
| `recorded/` | `llm_rewrites.jsonl` (query rewrites), `llm_judgments.jsonl` (relevance labels), `rerank.csv.gz` (cross-encoder scores) | recorded model answers, replayed in the lessons |
| `expected.json` | the expected NDCG@10 of the setup check | measured |

## The queries

- `W-nnn`: a real WANDS query in English (`source` wands).
- `F-nnn`: the French version of `W-nnn`, **machine-translated** by a language model (chat-small on Azure); it uses the judgments of `W-nnn`.
- `T-nnn`: `W-nnn` with one spelling mistake that our code made (**a practice problem we made on purpose**); same judgments.
- `C-nnn`: a product code typed as a query (planted); the product is the only exact result, nothing else is judged.
- `P-nnn`: "sofa", "couch", "canapé": planted broad queries, judged by a rule on the product class (sofa classes exact; sofa tables, covers and cushions irrelevant; everything else not judged).
- `qtype` (known-item, specific, broad) was written by a language model (recorded) for each WANDS query.
- `band` (head, torso, tail) comes from the synthetic log: the 40 most searched query texts are head, the next 120 torso, the rest tail.

## How the query log was made (synthetic)

Larkfield's search today (SQLite FTS5, every word must match, title and description) shows the top 10 products.
A position-based click model makes the clicks: a person looks at position k with probability 1/k, clicks a product
they look at with probability 0.65 (exact), 0.25 (partial) or 0.05 (irrelevant or not judged), and adds a clicked
product to the cart with probability 0.30, 0.08 or 0.01. Searches come from the public queries: 78% English WANDS
queries (short, broad queries are the most frequent: Zipf weights), 6% with a spelling mistake, 12% French, 2%
product codes, 2% the planted queries. After an empty page or no click, half of the people search again (the
corrected or English query, or a shorter query). The click model is in the project's `clicks.py`. These numbers
are our assumptions, not measurements of real people.

## Why this dataset

WANDS is a real product catalogue with real shoppers' queries and graded relevance judgments by people (a median
of about 200 judged products per query), under the MIT licence, small enough for a laptop. The Amazon Shopping
Queries dataset (ESCI, Apache-2.0) is much larger (its product file alone is about 1 GB) and is a case study of the
course instead.

## Changes we made

- Kept the home and garden departments (dropped business, school, food-service and service products).
- Renamed WANDS's house brand to Larkfield and gave every product a new ID.
- Kept a part of the products and of the queries for the course team (a held-out set and a final assignment);
  they are not here.
- Added the synthetic fields, the French titles and queries, the planted queries, the query log and the
  embeddings and recorded answers.

## The models

| Model | Use | Licence | Training data (the model card says) |
|---|---|---|---|
| `ibm-granite/granite-embedding-97m-multilingual-r2` | the bi-encoder (embeddings) | Apache-2.0 | data with permissive, enterprise-friendly licences and IBM data; MS MARCO not used |
| `ibm-granite/granite-embedding-reranker-english-r2` | the cross-encoder (re-ranking) | Apache-2.0 | the same; MS MARCO not used |
| chat-small (Azure) | French translations, query kinds, rewrites, relevance labels | recorded answers | — |

## Limitations and cautions

- The click log is synthetic: it shows how position bias works, not how many people click at Larkfield.
- The French queries are translations of English queries by a language model, so translating them back to English
  is easier than with real French queries.
- WANDS judged a pool of products for each query. A product that nobody judged counts as irrelevant, which is
  unfair to a search that finds good products nobody judged (the lessons measure this).
- Prices, stock and sale flags are random within simple rules: sale items are out of stock more often on purpose
  (a practice problem we made on purpose).

## WANDS licence

```
MIT License

Copyright (c) 2021 ecir2022

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
