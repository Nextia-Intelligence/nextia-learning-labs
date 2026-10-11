# Evidence card: build, buy or partner for invoice extraction

| Evidence | Label | Source | What it can and cannot show |
|---|---|---|---|
| Trial results: values right, complete documents, wrong and invented values, by kind of document | recorded | [Document and Multimodal AI](https://learning.nextia-ai.com/courses/document-ai/): 54 made-up receipt documents, 435 printed values | Shows how each **kind** of reading performs on varied receipts. Cannot show the vendors' real products, which are constructed. |
| Which product stands for which path | constructed | this case study | A fair stand-in, not a measurement of a real vendor. |
| The model's confidence: 9 of 10 wrong values at confidence 1.0 | recorded | same course | Shows that this model's confidence did not warn about its errors. |
| Share sent to a clerk (20.4%), wrong documents that reach the books (0/54 in-house, 3/54 with a confidence threshold) | recorded | same course | On 54 documents: one wrong document more or less changes the rate a lot. |
| In-house model cost per document (US$0.0018) | recorded (tokens × list price) | same course | Prices change: check the provider's current page. |
| Vendor and partner prices, fees, contracts, claims, data terms, exits | constructed | [the offers](offers.md) | Realistic, not real. In a real decision, read each provider's own terms page. |
| Volumes, minutes, clerk and engineering costs, error cost, upkeep, build hours | assumption | [cost ranges](cost-ranges.md) | Change them to your own; the method stays. |

## Known gaps (say them in your recommendation)

- The trial set is 54 receipt documents (synthetic); it has no multi-page supplier invoices.
- The partner has no result on Larkfield's documents.
- The partner's error cost is unknown (no trial): shown as none, not as zero.
- The documents are generated for the course: no real supplier, receipt or customer is in them.
- ScanLedger's "99.6% field accuracy" was measured on the vendor's own 500 sample invoices: not comparable with a result on Larkfield's documents.
