# Operations: running doc-extract next to the ticket system

## Asynchronous processing

A customer attaches a file to a ticket; the ticket system (`ticket-api`) stores the file and answers
at once. Reading the file takes from milliseconds (a digital PDF) to seconds (OCR) and, when the
model is needed, many seconds more. So the ticket system does not wait: it puts a job "read
attachment X of ticket T" in a queue (the scaling course's queue), and a worker runs
`pipeline.process` for it and stores the result next to the ticket. The agent sees "reading the
receipt..." until the result arrives, then the values with their boxes, or "needs review".

## Versions and reprocessing

Every result stores the versions that made it: the pipeline, the extraction contract, the OCR engine
and the model prompt (`pipeline.versions()`). When one of them changes, `python -m doc_extract.pipeline
status` lists the results made by an older version, and `reprocess` runs only those. Corrections made
by people are kept: a new extraction never replaces a person's correction (the correction is the
latest row; see `corrections.py`).

## Deletion

When a customer asks to delete their data, or the retention period ends, delete the original file in
the ticket system and run `python -m doc_extract.pipeline delete <document>`: it deletes the result, the
OCR cache and the review rows of that document, and writes one line (what, when, how many items; no
content) to `out/deletions.log`.

## Regression sets

`tests/regression/expected.json` holds the expected values and statuses of 15 documents, at least
one of each kind: digital, scanned, turned, photo, French, another shop, cut off, unreadable, a wrong
total, a claim with two parts, a copy, a damaged file, a wrong extension. `python -m doc_extract.pipeline
regression` must show no change before any new version goes live. When a change is meant (a better
OCR engine), update the file with `--update` and say in the change why each value changed.
