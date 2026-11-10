# larkfield-match: snapshots

The course project `larkfield-match` (the `match` command) at the start of the course and at the end of each
module. Each folder is a complete project with its own README, requirements and tests.

| Folder | When to use it | Tests |
|---|---|---|
| `start/` | Module 1, lesson 3 (*Meet the records*): the data reader, the exact baseline, pair measures, the setup check | 11 |
| `end-of-m02/` | After Module 2: normalising, parsing, rules, results by source and by practice problem | 16 |
| `end-of-m03/` | After Module 3: blocking keys, sorted neighbourhood, MinHash LSH, pair completeness | 21 |
| `end-of-m04/` | After Module 4: similarity measures, sound codes, comparison vectors, a weighted score | 25 |
| `end-of-m05/` | After Module 5: Fellegi-Sunter weights, Splink on DuckDB, review bands | 29 |
| `end-of-m06/` | After Module 6: pair classifiers, active learning, embeddings, recorded language-model answers | 34 |
| `end-of-m07/` | After Module 7: safe clustering, cluster measures, golden records, undo | 38 |
| `end-of-m08/` | After Module 8 (the end of the course): daily matching, review, timing, privacy, deletion requests | 42 |

Module 1 adds nothing after lesson 3, so there is no `end-of-m01/`: use `start/`.

Copy a folder to your own place, for example `projects/larkfield-match`, and follow its README. Keep the course
data at `../../data` from the project folder, or set `LARKFIELD_DATA` to its path. If your copy breaks, compare it
with the next folder, or start again from a fresh copy.
