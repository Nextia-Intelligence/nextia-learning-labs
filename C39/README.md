# Entity Resolution and Record Matching: Is This the Same Thing?

Materials for the course *Entity Resolution and Record Matching: Is This the Same Thing?* on
[learning.nextia-ai.com](https://learning.nextia-ai.com).

## What is in this folder

| Folder or file | What it is |
|---|---|
| `M01-L03-…` to `M08-L…` | One folder per lesson with a notebook: the learner notebook and its solution. Open them in Colab, Kaggle or VS Code. |
| `data/` | The Larkfield records (synthetic): three customer lists, two supplier feeds, the true customers and products, labelled pairs, a week of new records, embeddings and recorded model answers, with a dataset card and checksums. |
| `snapshots/` | The course project `larkfield-match` (the `match` command) at the start of the course and at the end of each module. |

Every notebook downloads what it needs by itself. To work on your own computer, use Python 3.12, open a snapshot
folder and follow its README.

## Where the data comes from

**Every record is synthetic.** Our code made the customers, the products, the errors in them and the labels from
invented people and products. No record describes a real person. The practice problems in the data (for example
two brothers who share an email) are ones we made on purpose. See `data/dataset-card.md`.

## Licences

The code is under the MIT licence. The data is under CC0 1.0. The embedding model that made `data/embeddings/`
(`ibm-granite/granite-embedding-97m-multilingual-r2`) is under the Apache-2.0 licence.
