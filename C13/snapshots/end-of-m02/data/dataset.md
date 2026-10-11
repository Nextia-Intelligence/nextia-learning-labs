# Dataset card: Larkfield's documents (made up for the course)

Used by: every lesson of *Document and Multimodal AI* and the project `doc-extract`.

| Field | Value |
|---|---|
| Source | Made by the project's generator: `python -m doc_extract.generate` (`doc_extract/generate.py`, seed 13) |
| Publisher / creator | Nextia Learning |
| Licence | CC0 1.0 (public domain dedication). The generator's code is MIT. |
| Attribution text | None needed. "Synthetic documents from Nextia Learning" is welcome. |
| Version | 1.0 (the version of `doc-extract` that made it) |
| Files | 65 documents in `documents/` (about 17 MB) and `truth.jsonl` (the true values); in the labs repository, `C13/data/` |
| SHA-256 | one line per file in `SHA256SUMS` (`python -m doc_extract.generate --check` compares them) |
| Size | 65 documents: 53 receipts, 2 policies, 1 price list (PDF), 1 spreadsheet, 1 warranty claim, 7 problem files |

## What one row means

One line of `truth.jsonl` is one document: its file, its kind (`receipt`, `policy`, `price_list`,
`spreadsheet`, `claim`, `bad`), how it was made (`source`: digital PDF, scanned PDF, scanned image,
phone photo, spreadsheet, mixed PDF; `conditions`: resolution, angle, blur, fading, cut-off parts),
the decision that intake should make, and the true values: for a receipt, the 9 fields of the
extraction contract (vendor, order number, date, currency, subtotal, shipping, tax, total, payment
method; `null` when the document does not show the field), the item lines and every printed line;
for a policy, its sections in reading order; for the price list and the spreadsheet, every product
row.

## Why this dataset

The course needs documents whose true values are known exactly, with the problems real documents
have, one at a time: a text layer or none, a crooked or turned scan, a phone photo with a shadow, low
resolution, French receipts (day first, decimal comma), another shop's layout, a total that does not
add up, a value that is cut off, a table that continues on the next page with merged cells, a
spreadsheet with units in the headers, a damaged file, a locked file, a file too large, a copy and a
second scan of the same receipt. Real receipts have personal data and no exact truth. A public receipt
set (with its own labels) is used in a case study instead.

## How the true values were made and checked

The generator writes each value and then draws it, so the value is known before the document exists.
The course author opened every document type and compared the printed values with `truth.jsonl`. For
a value that a photo cuts off, the truth is `null` (the photo cannot show it), and `printed_but_cut_off`
names it.

## Changes we made

None after generation. The same generator and the same package versions write the same bytes
(checked on macOS). Another operating system may draw pictures a few bytes differently: then
`--check` lists the files, and the numbers in the lessons can differ a little.

## Limitations and cautions

- All documents come from one program: real documents vary much more (fonts, paper, handwriting,
  stamps, folds, glare). Numbers measured here say what each method does on these problems, not how
  often the problems happen in real life.
- The receipts use 3 layouts. Rules written for them work well on them; that is the point of the
  comparison with an unknown layout (the partner shop), not a promise for other shops.
- The amounts, names and card endings are invented. Do not use the set to test anything about real
  shops or people.
