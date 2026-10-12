# Review queue: design (worked example)

Grace's team checks only the documents the pipeline cannot vouch for. This is the design that
`review.py` and `corrections.py` implement; the numbers come from the course's documents.

## What goes to the queue

| Reason | Where it comes from | Example |
|---|---|---|
| A validation error | `validate.py` | the total is not subtotal + shipping + tax; a required field is missing |
| A conflict | `combine.py` | the rules read one total, the model another |
| An unverified value | `combine.py` | the model gave a value that cannot be found on the page |
| Low certainty | `review.py` | the lowest OCR score of a required field is under the threshold |
| A possible duplicate | `validate.duplicates` | the same order number, or the same shop, date and total, as an earlier document |
| Stopped at intake | `intake.py` | damaged, locked with a password, too large |

The model's own confidence is not a reason: it says 0.95 or more for almost every answer, right or
wrong (`python -m doc_extract.review --calibration`).

## What the reviewer sees

One card per document: the picture of the page with the box of every field drawn on it
(`provenance.py`), the extracted values with their status (found, inferred, absent and why), the
reasons above, and for a conflict both values side by side.

## What the reviewer can do

- **Accept** the values: nothing changes; the decision is recorded.
- **Correct** a field: `python -m doc_extract.corrections correct D045 total 405.61 --reviewer Grace --note "..."`.
  The note is required. The extracted value stays in the database; the correction is a new row with
  the old value, the new value, who, when and why, and a version number.
- **Ask the customer** when the document does not show the value (a cut-off total): the field stays
  absent until the customer sends a better picture.

## Failed totals and uncertain vendor names (the module's task)

- A total that does not add up is an **error**: it always goes to the queue, whatever the
  certainty. The reviewer compares the printed lines with the picture; the shop may really have
  printed a wrong total (the course's documents D050 and D051 do).
- A vendor name that is not in Larkfield's list of shops is **unverified**: the reviewer checks the
  name on the picture and, if the shop is new, asks the purchasing team to add it to the list.
