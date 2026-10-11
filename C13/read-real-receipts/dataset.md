# Dataset card: CORD v2, test split (fixed sample)

Used by: the case study *Read real receipts* (Document and Multimodal AI, Module 7), the projects `starter.zip` and
`finished.zip` (`cord_eval`, `notebooks/evaluate-cord.ipynb`)

| Field | Value |
|---|---|
| Source | https://huggingface.co/datasets/naver-clova-ix/cord-v2 (the creators' page: https://github.com/clovaai/cord) |
| Publisher / creator | NAVER CLOVA |
| Licence | Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/ — stated by the creators on GitHub and on the Hugging Face card |
| Attribution text | CORD v2 by NAVER CLOVA, CC BY 4.0. Park, Shin, Lee, Lee, Surh, Seo and Lee, "CORD: A Consolidated Receipt Dataset for Post-OCR Parsing", Workshop on Document Intelligence at NeurIPS 2019. Changed by Nextia Learning (see below). |
| Version or access date | revision `7f0115a4b758a71d6473b8d085751692da2fef98` of the Hugging Face dataset, file `data/test-00000-of-00001-9c204eb3f4e11791.parquet` (234,202,795 bytes, SHA-256 `51c65f1788faff392abe2a0b55b023eb23e9be551c509138eaa3a832514224e7`) |
| File used | `data/cord-v2-test-sample.zip`, kept in this folder: yes (CC BY 4.0 allows redistribution with attribution and a note of changes) |
| SHA-256 | `2dd48e2cc1412d4cdcb41314f1ccad70901fc0c3f8126f7cf1554ed3fab3a900` (19,686,533 bytes); every file inside is listed in its `SHA256SUMS` |
| Size | 100 receipt pictures (JPEG) and 100 label records (`labels.jsonl`), 19.7 MB |

## What one row means

One record is one photo of one paper receipt from a shop, restaurant or café in Indonesia, with CORD's
labels: every printed word with its box and class (`valid_line`), and the parse (`gt_parse`): the menu
items (name, count, price), the subtotal, tax, service charge and discount, and the total, cash, change
and card amounts. The case study scores total, subtotal, tax, currency (IDR) and item lines against them.

## Why this dataset

The case study needs real receipts in a layout and a language that the course's rules have never seen,
with labels for fields the course's contract also has, under a clear permissive licence. CORD is the only
candidate whose creators state such a licence. SROIE (ICDAR 2019) labels vendor, date and total, a better
fit for the contract, but its licence is stated only by mirrors, not by its creators; WildReceipt has no
stated data licence. The comparison is in the case study's `DATASET-RESEARCH.md` (course authors' notes).

## Changes we made

- Only the 100 receipts of CORD v2's test split.
- Each picture converted from PNG to JPEG (quality 90); 17 pictures whose longer side was over 2,000
  pixels were made smaller to 2,000 pixels. `labels.jsonl` gives the scale; CORD's coordinates are
  unchanged (original pixels). Measured effect: the case study's rules read 253 of 301 labelled values on
  the sample and 257 on CORD's original PNG pictures.
- Our own IDs (`cord-test-000` = CORD test `image_id` 0) and a split: 40 "dev" receipts to adapt the rules,
  60 "test" receipts to measure once (a seeded shuffle, seed 13).
- The labels are unchanged (`ground_truth`, as CORD publishes it). `NOTICE.md` inside the zip says the same.

## Limitations and cautions

- **Not every field is labelled.** CORD removed the shop and payment labels ("due to Indonesian legal
  issues") and blurred shop names, addresses and card numbers in the pictures. Vendor, date, order number
  and payment method cannot be scored. Some printed totals have no label (for example `cord-test-037`), and
  a few labels sit on another line (`cord-test-018` and `cord-test-071` label a "Sub Total" line as the total).
- **Real receipts break textbook rules.** About four in ten labelled receipts do not satisfy
  "total = subtotal + tax": service charges, discounts, tax included in the prices, totals rounded to 100
  or 500 rupiah.
- **One country, one period, mostly restaurants.** Results do not carry over to other countries, shops or
  phones without a new measurement. 100 receipts (60 for the test) give rough numbers: one receipt is
  about 1.7 percentage points of the test.
- **Real people's purchases.** No names are labelled, but the receipts are real. Do not try to identify
  shops or people, and do not use the pictures for anything but learning and evaluation.
