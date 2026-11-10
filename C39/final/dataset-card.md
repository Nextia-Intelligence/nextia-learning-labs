# Dataset card: Fernhollow's customer records (synthetic)

Used by: the final assignment of *Entity Resolution and Record Matching: Is This the Same Thing?*

| Field | Value |
|---|---|
| Source | Made by the course's data generator (the same code as the Larkfield records), with a fixed seed |
| Publisher / creator | Nextia Learning |
| Licence | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/) |
| Attribution text | Synthetic customer records by Nextia Learning (no attribution needed) |
| Version or access date | Version 1 of the course data |
| File used | `fernhollow_customers.csv` and `labelled_pairs.csv`, kept in this folder: yes |
| SHA-256 | See `SHA256SUMS` |
| Size | 10,773 rows × 9 columns (`fernhollow_customers.csv`); 600 rows × 5 columns (`labelled_pairs.csv`); about 1 MB in all |

## What one row means

One row of `fernhollow_customers.csv` is one customer account in the till system of Fernhollow Home & Hardware,
an invented chain of hardware shops that Larkfield bought. There is no target column. The task is to find which
rows describe the same person as a Larkfield record, or as another Fernhollow row.

One row of `labelled_pairs.csv` is a pair of records with a label: 1 when the two records describe the same
person, 0 when they do not.

## Why this dataset

Real customer records are personal data and cannot be shared. Synthetic records let every learner work on the
same data, and they let the course team grade the answers, because our code knows the true person behind every
record. Fernhollow is new to the learner: a new schema and new habits test whether a matching pipeline built for
Larkfield transfers to another company.

## How the records were made

1. Some Fernhollow customers are people who are already in Larkfield's records. The others are new people, made
   in the same way as Larkfield's people (households, moves, family emails).
2. Some people have two records in Fernhollow's own list.
3. When a person's values are written into a record, the same error model as Larkfield's changes some of them:
   typing errors, nicknames, missing accents, an old address, short street words and postcodes written in
   another way. Every probability is a choice of ours.
4. Fernhollow's till system has its own habits. Look at the values: they are the first thing to understand.

Names come from lists of common first names and surnames. Towns and streets are invented. Phone numbers use the
555 exchange. Emails use reserved example domains.

## Changes we made

The public file has no true-customer column. The course team keeps it to grade the assignment. The labelled pairs
are a small sample, chosen as described in `README.md`.

## Limitations and cautions

- The records are synthetic. The error model is ours, so a method that works here may work less well on real
  records, and the reverse.
- The data has practice problems that we made on purpose. They are not listed here: finding them is part of the
  assignment.
- The labelled pairs have far more true pairs than a random set of candidate pairs. Precision measured on them is
  too high for your links.
- Do not try to find any real person behind these records. There is none.
