# Evaluation report: doc-extract on Larkfield's receipts (worked example)

Made with `python -m doc_extract.evaluate --systems text,ocr,ocr_prepared,vision,vision_v1,combined`
on the course's 54 receipt documents (53 receipts and the warranty claim's receipt page): 435
printed values of the 9 contract fields, and 51 fields that the documents do not show. The
documents are made by the course's generator; the vision answers are the course's recordings.

## Results by path

| Path | Printed values correct | Missing | Wrong | Invented | Complete documents |
|---|---|---|---|---|---|
| PDF text layer + rules | 169 of 435 (38.9%) | 266 | 0 | 0 | 19 of 54 (reads only digital PDFs: 96.5% of their values) |
| OCR + rules | 392 (90.1%) | 42 | 1 | 0 | 44 |
| OCR on prepared pictures + rules | 408 (93.8%) | 27 | 0 | 0 | 46 |
| Vision model, plain prompt (v1) | 424 (97.5%) | 8 | 3 | **11** | 40 |
| Vision model, precise prompt (v2) | 425 (97.7%) | 9 | 1 | 0 | 51 |
| **Combined (the pipeline)** | **427 (98.2%)** | 8 | 0 | 0 | **53** |

A document is complete when every required field is right and nothing is invented. The 11 invented
values of prompt v1 are all order numbers: on in-store receipts it copied the transaction number
(for example `0693-220` on D003). The combined pipeline calls the model for 9 of 54 documents
(the 6 receipts of the other shop and 3 photos with missing fields), for US$0.097 in total, about
US$0.0018 per document, instead of US$0.0113 per page for the model on every page.

## Error analysis by document type

- **Digital PDFs:** the text layer is exact and fast (5.4 ms per page). The rules miss only the
  other shop's words (D017, D018); the model fills them. The model alone misread "LARKFIELD" as
  "LARKEFIELD" on a clean digital receipt (D009): a text layer does not make that mistake.
- **Scans:** without preparation, OCR fails on the turned pages (D025 at 90°, D026 at 180°);
  preparation turns them upright, and every scanned PDF is then complete.
- **Photos:** the hard cases are the photos that miss part of the receipt. D045 has no total in the
  picture and D047 no shop name and no date: every path, correctly, returns them absent. D046 is
  unreadable: OCR finds no text and the model says "unreadable"; its 8 printed values are the
  combined pipeline's only misses, and the document goes to review.
- **Validation** catches the two receipts whose printed total does not add up (D050, D051), on
  every path that reads them: the values are read correctly; the document is wrong.

## What this does not show

The documents come from one generator with three layouts. Real documents vary more; build a
regression set from real (consented, anonymised) files before trusting these numbers for Larkfield.
