# Dataset card: DBLP-ACM (Leipzig benchmark datasets for entity resolution)

Used by: the case study *Link bibliographic records* of *Entity Resolution and Record Matching: Is This the Same Thing?*, `link-bibliographic-records.ipynb`

| Field | Value |
|---|---|
| Source | https://dbs.uni-leipzig.de/research/projects/benchmark-datasets-for-entity-resolution (file `/files/datasets/DBLP-ACM.zip`) |
| Publisher / creator | Database group of Prof. Erhard Rahm, University of Leipzig |
| Licence | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The source page says: "January 2019: These datasets are made available by the database group of Prof. Erhard Rahm under the Creative Commons license", linked to CC BY 4.0, and "To give proper credit please refer to this website and the VLDB2010 paper". |
| Attribution text | "Benchmark datasets for entity resolution" by the database group of Prof. Erhard Rahm, University of Leipzig, https://dbs.uni-leipzig.de/research/projects/benchmark-datasets-for-entity-resolution, CC BY 4.0. Paper: H. Köpcke, A. Thor, E. Rahm, "Evaluation of entity resolution approaches on real-world match problems", PVLDB 3(1), 2010, 484–493. |
| Version or access date | The files inside the zip are dated 30 September 2010. The licence statement was checked on the source page when the case study was built. |
| File used | `DBLP-ACM.zip`, kept in `data/`: no (the notebook downloads it from the source and checks the checksum) |
| SHA-256 | `e37e7ed8e06722499e6d9e94583fdec279207b13ce6270a37595b6a5d594bc40` (270,239 bytes) |
| Size | DBLP2.csv 2,616 rows × 5 columns (id, title, authors, venue, year; the source page says 2,614); ACM.csv 2,294 × 5; DBLP-ACM_perfectMapping.csv 2,224 true links. DBLP2.csv is Latin-1 text; ACM.csv writes non-English letters as HTML codes (`Bj&#246;rn`). |

## What one row means

One row of `DBLP2.csv` or `ACM.csv` is one published paper (or editorial, review, interview) as one library lists it: its title, its authors, the venue (conference or journal) and the year. One row of the mapping file is a true link: a DBLP record and an ACM record of the same paper. The case study predicts, for a pair of records, whether they describe the same paper.

## Why this dataset

Real records from two curated bibliographic libraries, with the true links known, small enough for a laptop and a free notebook (270 KB). It is cleaner than product data: the year always agrees, the venues map one to one, and most titles agree after normalising. So simple rules do well, and the case study can show where they still fail: titles that many papers share, changed titles, author lists in another order. Compared and not used: DBLP-Scholar from the same page (64,263 Scholar records, too large for the free notebook) and a dblp–OpenAlex link built by DOI (both CC0; suggested as a portfolio extension).

## Changes we made

None to the benchmark files. The notebook reads them as they are. Shipped next to the notebook, made by Nextia Learning from the titles:

- `data/embeddings/`: the embedding of every title (DBLP and ACM) from `ibm-granite/granite-embedding-97m-multilingual-r2` (Apache-2.0, revision `835ad14087e140460703cf0fae09f97d469d65c2`, 384 numbers, stored as 8-bit integers with one scale per row), with the IDs in the same order, and `model.json`.

## Limitations and cautions

- **Old and narrow.** Database papers from five venues, 1994 to 2003. Today's records have DOIs, preprints and many more venues.
- **Not every record has a partner.** 392 DBLP records (292 of them from 2002 and 2003; 239 from VLDB) and 70 ACM records have no link.
- **The labels are a judgement.** The benchmark's authors made the links; a few may be wrong or missing.
- **Real names.** The author names are real researchers, listed in their public role as authors. Nothing in the case study is a claim about any person.
