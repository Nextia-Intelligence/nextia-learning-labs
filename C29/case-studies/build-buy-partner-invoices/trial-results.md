# Trial results on Larkfield's documents

*The results are **recorded** in the course [Document and Multimodal AI](https://learning.nextia-ai.com/courses/document-ai/), on its 54 made-up receipt documents (digital PDFs, scans, phone photos, two shops' layouts, English and French), with 435 printed values to read. Which product works like which recorded path is **constructed** for the case study.*

| | In-house (rules + model + check) | ScanLedger (vision model on every page) | FormGrid (templates) | Partner |
|---|---|---|---|---|
| Printed values read right | 427 of 435 (98.2%) | 425 of 435 (97.7%) | 408 of 435 (93.8%) | no trial |
| Documents complete and right | 53 of 54 | 51 of 54 | 46 of 54 | no trial |
| Values read wrong | 0 | 1 | 0 | no trial |
| Values invented (a value the document does not show) | 0 | 0 | 0 | no trial |
| Phone photos: values right | 93.2% | 92.3% | 87.2% | no trial |
| How documents reach a clerk | errors and missing values: 20.4% of documents | only below a confidence threshold | documents it cannot read: 14.8% | the partner's staff check |
| Documents with a wrong or missing value that reach the books | 0 of 54 | 3 of 54 | 0 (it read no value wrong; what it cannot read goes to a clerk) | unknown |

## The model's confidence (recorded)

The vision model gave a confidence for each of 486 values. Its lowest confidence was 0.96. It was wrong 10 times, and **9 of those 10 wrong values had the highest confidence, 1.0**. Most of them were on a photo nobody could read: the model said "absent" with full confidence.

**What this tells us.** A threshold on the model's own confidence sends almost nothing to a clerk, so its wrong values go straight to the books. The in-house option catches errors with checks that do not trust the model: the lines must add up to the total, and every required value must be present.

## Another finding (recorded)

With a looser instruction (an earlier prompt), the same vision model **invented 11 order numbers**: it copied another number from the receipt into the order-number field. A better prompt removed them. A vendor's demo does not tell you which instruction its product uses.

## Known gaps

- The trial set is 54 receipt documents (synthetic); it has no multi-page supplier invoices.
- The partner has no result on Larkfield's documents.
- The partner's error cost is unknown (no trial): its cost is '+ errors', never zero.
