# Dataset card: Shopping Queries Dataset (ESCI), a fixed sample (English and Spanish)

Used by: the case study *Shopping queries with hard negatives* of the course *Search and Ranking: Find the Best Match*, `shopping-queries-with-hard-negatives.ipynb`

| Field | Value |
|---|---|
| Source | https://github.com/amazon-science/esci-data (folder `shopping_queries_dataset/`) |
| Publisher / creator | Amazon; Chandan K. Reddy, Lluís Màrquez, Fran Valero, Nikhil Rao, Hugo Zaragoza, Sambaran Bandyopadhyay, Arnab Biswas, Anlu Xing and Karthik Subbian |
| Licence | Apache-2.0 ("This project is licensed under the Apache-2.0 License", README of the repository; `LICENSE` at commit `7916cdf6ab75a462e77f20ab40428a10923998d5`). A copy of the licence is `data/LICENSE-ESCI.txt`; the NOTICE is `data/NOTICE-ESCI.txt`. |
| Attribution text | Shopping Queries Dataset: A Large-Scale ESCI Benchmark for Improving Product Search (Reddy, Màrquez, Valero, Rao, Zaragoza, Bandyopadhyay, Biswas, Xing and Subbian, 2022, arXiv:2206.06588), https://github.com/amazon-science/esci-data, Apache-2.0. Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. Sample and changes by Nextia Learning. |
| Version or access date | Commit `7916cdf6ab75a462e77f20ab40428a10923998d5` |
| Files used | `esci_queries.csv`, `esci_judgments.csv.gz`, `esci_products.csv.gz`: a sample made by the course team (below), kept in `data/`: yes (Apache-2.0 allows redistribution with the licence and a notice of changes) |
| SHA-256 | esci_queries.csv `449213c0cf43043717ffc4e692ab0bb570db3e18d4c29bb4e0d55396eaf7cdce`; esci_judgments.csv.gz `2bc8ed25b3fb511e2d788570032dbe74bfeeead9dfba6ae3f82d316276af4ae1`; esci_products.csv.gz `2fa0682a01cff6d7ac44ef3a22a2b6ca1137df38bca825030482026e412d98b6`; esci_product_embeddings.npy `24e63d044de06b87bb9fa3c7800a136366bebf05fb581ea8e8766c598fef01c6`; esci_query_embeddings.npy `f37a40e0b52b217126bb81b4441cc5f57285480afd4efc40c982a9c36680d5ee`; esci_rerank_scores.csv.gz `6e305db12eaa9237d82efc84a93ca851980cf7dbdfbecd065f7801fa0f21bad8`; esci_latency_ms.csv `4ed83a25165b006f5aa29c766bdcfb9db2f0afee3fd415f3f8eb804e33c7d231`; model.json `10b3be3327b4208bd79f7aa936a8076c9610e7c5cd5889a592d40590a51db168` |
| Size | queries 1,400 × 5; judgments 33,945 × 3; products 32,759 × 7 (39.8 MB in all with the course team's files) |

## What one row means

`esci_queries.csv`: one search query typed on Amazon's US (`us`) or Spanish (`es`) site, its split in ESCI (train or test) and ESCI's `source` tag (`negations`, `parse_pattern`, `behavioral`, `nlqec` or `other`). `esci_judgments.csv.gz`: one label by a trained annotator for one product that Amazon's search showed for the query: **E**xact (the product asked for), **S**ubstitute (does not match every detail but could replace it), **C**omplement (does not match but goes with it, such as an accessory) or **I**rrelevant. `esci_products.csv.gz`: one product of one site: title, brand, colour, bullet points and description. The labels are the target of the evaluation.

## Why this dataset

Four labels that separate a substitute and a complement from a miss, and candidates that are the look-alikes a real search showed (hard negatives), in English and Spanish, with a permissive licence. Compared with WANDS (MIT; three labels, English, the course's own base data) and two Kaggle competition sets (Home Depot, Crowdflower) whose terms do not allow reuse as far as we found. See `reference/c38/m09/cs2/DATASET-RESEARCH.md` in the site repository.

## Changes we made

The original files are `shopping_queries_dataset_examples.parquet` (SHA-256 `4a735b693b4a424a6fc67f5be6e4c811495c488bbf66d02a602d308b2744263a`), `shopping_queries_dataset_products.parquet` (`25124442d064d64b26f74082d6fa09438d679efc0c183cf28d19064a2b65a265`, 1.1 GB) and `shopping_queries_dataset_sources.csv` (`a5fed8ecc016443de40bf3c63098f0e3f23bbe4daa4236f1c38b8c3184778c50`). From them, `reference/c38/m09/cs2/prepare.py` made this sample:

- only the reduced version (`small_version` = 1, the data of the KDD Cup 2022's task 1), and only English (`us`) and Spanish (`es`);
- 400 test and 300 train queries per language, drawn at random (seed 38) from ESCI's own split, with every judged product of those queries;
- files converted from Parquet to CSV; columns renamed (`product_title` → `title`, `product_locale` → `locale`, …); the query's `source` joined in from the sources file;
- bullet points and description cut to their first 1,000 characters.

Files the course team added in `data/` (made by `prepare.py`):

| File | What |
|---|---|
| `esci_product_embeddings.npy` | 32,759 × 384 (float16), one row per product in file order; IBM `granite-embedding-97m-multilingual-r2` (Apache-2.0), text = title + brand + colour |
| `esci_query_embeddings.npy` | 1,400 × 384 (float16), one row per query in file order, same model |
| `esci_rerank_scores.csv.gz` | the cross-encoder score of every test candidate: IBM `granite-embedding-reranker-english-r2` (Apache-2.0; English only) |
| `esci_latency_ms.csv` | milliseconds of each search stage for 80 test queries, measured on an Apple M4 laptop (1 thread) |
| `model.json` | both models, their revisions and settings |

## Limitations and cautions

- **A sample.** 800 test queries (400 per language) give intervals of about ±0.02 NDCG@10; the full test split has 11,373 English and Spanish queries.
- **The candidates are fixed.** Every query's list is what Amazon's search showed. Ranking them is the task 1 of ESCI (re-ranking); the data cannot tell how well a method finds products that the shop's search missed.
- **Almost every query has an exact product** in the reduced version. The case study's "no exact product" case is constructed by hiding them.
- **One label per pair**, by annotators; the guidelines are in the paper. Substitutes and complements depend on the annotator's reading of the query.
- **Real brand and product names** are part of the data, not endorsements. Some product text is in another language than its site.
- **Text cut to 1,000 characters** for bullet points and descriptions; titles are complete.
