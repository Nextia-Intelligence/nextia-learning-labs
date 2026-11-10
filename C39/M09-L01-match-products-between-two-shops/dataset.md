# Dataset card: Abt-Buy and Amazon-GoogleProducts (Leipzig benchmark datasets for entity resolution)

Used by: the case study *Match products between two shops* of *Entity Resolution and Record Matching: Is This the Same Thing?*, `match-products-between-two-shops.ipynb`

| Field | Value |
|---|---|
| Source | https://dbs.uni-leipzig.de/research/projects/benchmark-datasets-for-entity-resolution (files `/files/datasets/Abt-Buy.zip` and `/files/datasets/Amazon-GoogleProducts.zip`) |
| Publisher / creator | Database group of Prof. Erhard Rahm, University of Leipzig |
| Licence | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The source page says: "January 2019: These datasets are made available by the database group of Prof. Erhard Rahm under the Creative Commons license", linked to CC BY 4.0, and "To give proper credit please refer to this website and the VLDB2010 paper". |
| Attribution text | "Benchmark datasets for entity resolution" by the database group of Prof. Erhard Rahm, University of Leipzig, https://dbs.uni-leipzig.de/research/projects/benchmark-datasets-for-entity-resolution, CC BY 4.0. Paper: H. Köpcke, A. Thor, E. Rahm, "Evaluation of entity resolution approaches on real-world match problems", PVLDB 3(1), 2010, 484–493. |
| Version or access date | The files inside the zips are dated 30 September 2010. The licence statement was checked on the source page when the case study was built. |
| File used | `Abt-Buy.zip` and `Amazon-GoogleProducts.zip`, downloaded from the source by the notebook, kept in `data/`: no (the notebook downloads them and checks the checksum) |
| SHA-256 | `Abt-Buy.zip` `b9ff2937d97371b7a00b0a97033213bfbdee24e8f1a0718a41ea8364472a8ff8` (134,745 bytes); `Amazon-GoogleProducts.zip` `fcd72e223d51ce5b0d6b1d68034a438ba95cf2940431e209a57910b067cc4811` (904,417 bytes) |
| Size | Abt.csv 1,081 rows × 4 columns (id, name, description, price); Buy.csv 1,092 × 5 (+ manufacturer); abt_buy_perfectMapping.csv 1,097 true matches. Amazon.csv 1,363 × 5 (id, title, description, manufacturer, price); GoogleProducts.csv 3,226 × 5; 1,300 true matches. Latin-1 text. |

## What one row means

One row of `Abt.csv` or `Buy.csv` is one product offer in one online shop: its title, a description and often a price. One row of the mapping file is a true match: an Abt offer and a Buy offer that are the same product. The case study predicts, for a pair of offers, whether they are the same product.

## Why this dataset

Real product titles from two shops, with the true matches known, small enough for a laptop and a free notebook (about 1 MB together). The titles show the problems of the course: model numbers written in several ways, sizes in inch marks, accessories that share words with their product, many missing prices. Amazon-GoogleProducts, from the same page, is the harder variant (software with versions and editions; most Google offers have no partner). Compared and not used: WDC Products (no data licence stated) and the Magellan/DeepMatcher files (no licence stated; their source page is gone).

## Changes we made

None to the benchmark files. The notebook reads them as they are. Shipped next to the notebook, made by Nextia Learning from the titles:

- `data/embeddings/`: the embedding of every product title (Abt, Buy, Amazon, Google) from `ibm-granite/granite-embedding-97m-multilingual-r2` (Apache-2.0, revision `835ad14087e140460703cf0fae09f97d469d65c2`, 384 numbers, stored as 8-bit integers with one scale per row), with the IDs in the same order, and `model.json`.
- `data/recorded/llm_band.jsonl`: 186 recorded answers of a small chat model (Azure chat-small, model `gpt-6-luna-2026-09-22`) for validation and test pairs near the review band, with the model's text, tokens, US$ and seconds. Recorded once; the notebook never calls a model.

## Limitations and cautions

- **Every product has a partner** in Abt-Buy. Real catalogues have many products without one, so one-to-one matching looks better here than it will in real work.
- **Old, small, one kind of product.** Electronics offers from 2010-era shop websites, about 1,000 per shop.
- **The labels are a judgement.** Some true matches are disputable (a Canon SD card and a Simpletech SD card with the same part number), and Amazon-Google seems to miss some matches.
- **Real brands.** The data names real brands and products as the shops listed them. Nothing in the case study is a claim about any shop or brand.
- No personal data.
