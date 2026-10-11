# Dataset card: Theo's weak capstone (constructed) and the two-shop data pack

Used by: the case study *Review a weak capstone* (`C27-M08-L02`), `starter.zip` and `finished.zip`

| Field | Value |
|---|---|
| Source | Built by the course team from the course-end project of *Portfolio Capstone: Build, Evaluate and Ship an AI Product* (`reference/c27/m08/l02/build.py` in the nextia-learning repository) |
| Publisher / creator | Nextia Learning |
| Licence | Code: MIT (`theo-doc-assistant/LICENSE`). Data pack: CC0 1.0, https://creativecommons.org/publicdomain/zero/1.0/ |
| Attribution text | "Weak capstone for review, constructed by Nextia Learning (MIT); data pack CC0." Not required by the licences; please keep it. |
| Version or access date | Course-end `doc-assistant` 1.0.0; Theo's repository at commit `2337087`, the resubmission at `600d7f9` |
| File used | `starter.zip` and `finished.zip`, kept in this folder: yes |
| SHA-256 | see `SHA256SUMS` next to the zips (made when the lead copies them) |
| Size | Theo's repository: 9 commits, 168 files, 51 documents, 103 questions (41 reserved as held-out, 38 left after Theo's change), 353 recorded answers. `starter.zip` about 1.1 MB, `finished.zip` about 2.3 MB |

## What one row means

There are no rows. The unit of review is the submission: one Git repository with its history. Inside it, one document is a shop's policy, and one line of `evaluation/questions.jsonl` is one question with its shop, date, kind and answer key.

## Why this dataset

The rubric's checks (wrong-shop isolation, the held-out lock, citation checks, a secret scan) only work on a project with two shops, a reserved question set and recorded answers. The course's own project has all of them and runs without a key or money. A known set of planted problems lets a learner check their review. A real person's repository was rejected: often no licence, no answer key, and an unfair public review of a real person. Details: `reference/c27/m08/l02/DATASET-RESEARCH.md`.

## Changes we made

Seven planted problems, in seven of Theo's nine commits (the answer key is in `finished.zip`, `reviewer-kit/review.md`). The "secrets" committed in the history are made-up values from a fixed seed; they never worked anywhere. Theo Marsh, the dates and the commit messages are invented.

## Limitations and cautions

- **Constructed.** The problems are typical, but they were planted on purpose. A real weak capstone has fewer obvious clues, and some problems that no checklist finds.
- The documents, shops and people are synthetic. Do not draw conclusions about real shops.
- The answers are recorded (real answers of chat-small, replayed). Tested on macOS (Apple silicon) only; the Windows and Linux commands are written, not run.
