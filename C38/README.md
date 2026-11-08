# Search and Ranking: Find the Best Match

Materials for the course *Search and Ranking: Find the Best Match* on
[learning.nextia-ai.com](https://learning.nextia-ai.com).

## What is in this folder

| Folder or file | What it is |
|---|---|
| `M01-L03-…` to `M09-L03-…` | One folder per lesson: the learner notebook and its solution. Open them in Colab, Kaggle or VS Code. The case-study folders also have their own `data/` and `dataset.md`. |
| `data/` | The Larkfield catalogue, the queries with their judgments, the synthetic query log, embeddings and recorded model answers, with a dataset card and checksums. |
| `compare.py` | The ranking measures and the comparison table: every lesson scores a search the same way. |
| `final/` | The final assignment's new season: new products and new queries, without judgments. |
| `snapshots/` | The course project `larkfield-search` (the `search` command) at the start and at the end of each module. |

Every notebook downloads what it needs by itself. To work on your own computer, use Python 3.12, open a snapshot
folder and follow its README.

## Where the data comes from

The products, the queries and the relevance judgments are derived from WANDS, the Wayfair ANnotation DataSet
(MIT licence). We renamed the shop to Larkfield and gave the products new IDs. The query log with its clicks, and
the prices, stock and sale flags, are **synthetic**: our code made them. The French titles and French queries were
**machine-translated** by a language model. The data has no real customer in it.

## Licences

The code is under the MIT licence. The data is under the MIT licence of WANDS (see `data/dataset-card.md`).
The models that the course uses have their own licences (Apache-2.0); see the dataset card.
