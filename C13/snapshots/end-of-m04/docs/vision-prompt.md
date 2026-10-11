# The vision-model request: design notes

The course recorded two prompts on every receipt page (`doc_extract/vision.py`).

| | Prompt v1 (plain) | Prompt v2 (precise) |
|---|---|---|
| Output | free JSON (`response_format: json_object`) | a strict JSON schema: for each field `value`, `printed`, `status`, `reason`, `confidence` |
| Absent values | not mentioned | "set value to null, status absent, reason not_printed / cut_off / unreadable; never guess, compute or complete a value" |
| Formats | not mentioned | dates `YYYY-MM-DD`, money with 2 decimals, Quebec dates day first, tax = sum of tax lines |
| Order number | not mentioned | "a transaction or invoice number is NOT an order number" |

Compare them yourself: `python -m doc_extract.vision D003 --prompt v1` and `--prompt v2`.
`python -m doc_extract.evaluate --systems vision_v1,vision` counts the invented values of each.

## What to send

- **Only the page that matters.** The warranty claim (D058) has two pages; only page 2 is a receipt:
  `vision.py` sends `receipt_page` only.
- **A crop when the document is small on the page.** A till receipt scanned on a letter page fills
  a quarter of the picture. `--crop` sends only the receipt (`prepare.content_box`): fewer image
  tokens for the same text (`recordings/vision-v2-crop.jsonl`).
- **Not too small.** Pictures are drawn at 150 dpi and at most 1,600 pixels on the longer side.
  `recordings/vision-v2-half.jsonl` and `-quarter.jsonl` hold answers for the same six pictures at
  half and a quarter of their size.

## What the answer is not

- Not evidence: the model gives no box. `combine.ground` looks for each value on the OCR lines; a
  value that cannot be found there is `unverified`.
- Not a probability: the `confidence` the model gives is almost always 0.95 or more, right or wrong
  (`python -m doc_extract.review --calibration`).
- Not repeatable to the letter: the same page sent twice can give a different answer
  (`recordings/vision-v2-pass2.jsonl`).
