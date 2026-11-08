# Dataset card: ArguAna (BEIR version)

Used by: Search and Ranking, case study *Search a help centre or a scientific corpus*, `search-a-help-centre-or-a-scientific-corpus.ipynb`

| Field | Value |
|---|---|
| Source | ArguAna Counterargs, https://zenodo.org/records/3973258 (DOI 10.5281/zenodo.3973258). The notebook downloads the BEIR version: https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/arguana.zip |
| Publisher / creator | Henning Wachsmuth, Shahbaz Syed and Benno Stein (the corpus, from the debate portal idebate.org); Nandan Thakur and others (the BEIR version) |
| Licence | **CC BY 4.0** (Creative Commons Attribution 4.0 International, https://creativecommons.org/licenses/by/4.0/), as stated on the Zenodo record. The BEIR download page states no licence of its own. |
| Attribution text | ArguAna Counterargs corpus by Henning Wachsmuth, Shahbaz Syed and Benno Stein (DOI 10.5281/zenodo.3973258), CC BY 4.0, in the BEIR version by Thakur et al. (2021). Changes: we split the queries into validation and test, and we computed embeddings and model scores. |
| Version | BEIR `arguana.zip` (files dated 2021-01-22); MD5 `8ad3e3c2a5867cdced806d6503f29b99`, as on BEIR's list of datasets |
| File used | `arguana.zip` (3.8 MB), downloaded from the BEIR source; **not** kept in `data/` (small and stable at the source; CC BY 4.0 would allow a copy) |
| SHA-256 | `cfdf79adce27a401b3cd3ea267903134dbfab2c6afeb95d7fe5724a00bf7557b` (`arguana.zip`) |
| Size | `corpus.jsonl` 8,674 documents (`_id`, `title`, `text`, `metadata`); `queries.jsonl` 1,406 queries (`_id`, `text`, `metadata`); `qrels/test.tsv` 1,406 judgments (`query-id`, `corpus-id`, `score`); 11.7 MB unzipped |

## What one row means

A **document** is one argument from a debate page: a point or a counter-point, a paragraph of about 150 words. A **query** is a point. Its one judgment names its **best counter-argument**: the counter-point written for that point on the same debate page. The task is to rank that counter-point high among all 8,674 documents.

## Why this dataset

Its licence is on the course's allowed list, it is small, and it is a real search task with long queries (median 174 words), so it shows where long queries change what works. SciFact (abstracts under ODC-By 1.0, not on the list), SciDocs (data files hosted elsewhere, terms not confirmed) and doc2dial (help pages of public services; no licence on the source page) were compared and not used. No help-centre search set with an allowed licence was found. Details: `reference/c38/m09/cs3/DATASET-RESEARCH.md` in the site repository.

## Changes we made

The ArguAna files are used unchanged. The course team added these files in `data/` (CC BY 4.0, like the corpus they come from):

| File | Size | SHA-256 |
|---|---|---|
| `data/split.csv` | 0.10 MB | `ca74391e8197cf741c48ad0c3531afc07838e55e1c93da08c997f76e99a5cf26` |
| `data/embeddings/docs.npy` | 6.66 MB | `5902a582f1557f75ea9c4fafe919d45ffd134335bb19607e541b6fa9d92e7e58` |
| `data/embeddings/queries.npy` | 1.08 MB | `213fef379bfada8bde2b70ea818234f1c7eb538526677d476ec54c3383856273` |
| `data/embeddings/queries-128.npy` | 1.08 MB | `60aa25f979e7cad0a688f3f8773432683786978a0d0cafb43bb7bbbb3bc8a66d` |
| `data/embeddings/model.json` | 0.00 MB | `0da7dd7757837ee0f373fe316d5d94a9b49548fe06d62680f38f1502231b018d` |
| `data/recorded/rerank.csv.gz` | 0.25 MB | `d5255e12e80ef759bc9ff7530deb157b0a0e665b94c27ee5d731ea706d7a661a` |
| `data/recorded/timing.json` | 0.00 MB | `a3273a0f0e135a7df8cb33adda874f4b9682f766a697029b66e6d514debdd84d` |
| `data/recorded/new-argument.npy` | 0.00 MB | `01a0a13770aa279e5683597aafac57b3c709ac7d668ab7ed13288a5a4b235ede` |

- `split.csv`: validation 409 and test 997 queries, split **by debate page** (189 pages, seed 38), so no page has queries on both sides; `words` is the query's length in words.
- Embeddings: IBM granite-embedding-97m-multilingual-r2 (Apache-2.0, revision `835ad140…`), the `text` field only (the `title` field holds topic tags), up to 512 tokens (`queries-128.npy`: up to 128 tokens), length 1, float16, on a laptop CPU.
- `recorded/rerank.csv.gz`: scores of IBM granite-embedding-reranker-english-r2 (Apache-2.0, revision `d09d3d69…`, up to 512 tokens) for the top 20 documents of the hybrid blend (alpha chosen on validation) of every query.
- `recorded/timing.json`: live milliseconds per query of each stage, 40 test queries, 1 and 4 threads, Apple M4.
- `recorded/new-argument.npy`: the embedding of one argument written by the course team (not in ArguAna).

The notebook reads the one judged document of each query as grade 2 ("exact" in the course's words), so that `compare.py`'s recall and MRR count it.

## Limitations and cautions

- **One judged document per query.** Other good counter-arguments count as wrong. Scores are lower bounds, and a method that finds another good answer is punished.
- **1,298 queries are also documents**, with the same text. Leave out the query's own document (the BEIR rule), or the query finds itself first.
- **5 judged documents are missing** from the corpus: those queries score 0 for every method. 218 documents share their text with another document.
- The arguments are opinions written by debaters on political, social and moral topics. A result is an argument, not a fact. The topics and the English come from one debate portal.
- The model cards of the Granite models do not name ArguAna in their training data; the bi-encoder's card reports a benchmark (MTEB Retrieval, English v2) that includes ArguAna. We cannot rule out that the models were tuned on similar data (vendor claims, not checked).
