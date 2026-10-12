# doc-extract

A small Python pipeline that reads the documents attached to Larkfield's help-desk tickets
(receipts as PDFs, scans and phone photos, a supplier price list, a spreadsheet, the shop's
policies) and keeps the **source of every value**: the file, the page and the box on the page, or
the sheet and the cell.

This project belongs to the course *Document and Multimodal AI* on Nextia Learning. Every document
in it is made up by the project's own generator: no real person, shop receipt or card number is in it.

## Set up (once)

You need Python 3.12 or later. macOS or Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m doc_extract.generate --check
python -m pytest -q
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m doc_extract.generate --check
python -m pytest -q
```

`generate` writes the course's 65 documents to `data/documents/` and their true values to
`data/truth.jsonl` (about 17 MB, 10 seconds). `--check` compares every file with the course's
checksums. If your files differ (another system can draw a picture a few bytes differently), your
numbers can differ a little from the lessons; to use the course's exact files, copy `documents/` and
`truth.jsonl` from the labs repository (`C13/data/` there) into `data/`.

You need no account, no key and no money. OCR runs on your computer's CPU (no download: the OCR
models are inside the `rapidocr` package). The vision model's answers were recorded by the course
team; the project replays them.

## Use it

```sh
python -m doc_extract.documents               # the 65 documents
python -m doc_extract.documents D036          # one document and its true values
python -m doc_extract.show D036               # a picture of each page in out/show/
```

Module 1: look inside the files.

```sh
python -m doc_extract.route                   # the format and the route of every page: text, ocr, sheet, stop
python -m doc_extract.textlayer D011          # the text layer of a digital PDF, with boxes
python -m doc_extract.layout D054             # reading order on a page with two columns
python -m doc_extract.contract                # the extraction contract (docs/extraction-contract.md)
```

Module 2: get the text out.

```sh
python -m doc_extract.intake                  # size, format, damaged, password, duplicate
python -m doc_extract.ocr D036                # OCR with boxes and scores
python -m doc_extract.vision D036             # the recorded vision-model answer (nothing is sent)
python -m doc_extract.compare D036            # the three paths on one document
python -m doc_extract.compare --all           # every receipt (OCR of all pages: about a minute the first time)
python -m doc_extract.prepare D025            # turn, straighten, crop and enlarge before OCR
```

OCR results are kept in `out/cache/ocr/`, so a second run is fast. Delete `out/` to start again.

Module 3: keep the structure and the source.

```sh
python -m doc_extract.sections D054           # headings, paragraphs, lists, footnotes
python -m doc_extract.tables D056             # a table over two pages with merged cells
python -m doc_extract.sheets D057             # the same list as a spreadsheet
python -m doc_extract.provenance D036         # every value with its page and box; a picture in out/evidence/
```

Module 4: use the vision model only where it helps.

```sh
python -m doc_extract.vision D003 --prompt v1 # the plain first prompt: it invents an order number
python -m doc_extract.combine D017            # rules where they work, the model where they do not
python -m doc_extract.uncertainty D047        # what the pipeline cannot know from this photo
```

Module 5: check before anyone trusts a value.

```sh
python -m doc_extract.validate D050           # a total that does not add up
python -m doc_extract.review                  # the review queue (out/review-queue.json)
python -m doc_extract.review --sweep          # review rate and wrong totals at each threshold
python -m doc_extract.review --calibration    # the model's own confidence against the truth
python -m doc_extract.corrections load D045
python -m doc_extract.corrections correct D045 total 405.61 --reviewer Grace --note "From the paper receipt"
python -m doc_extract.corrections history D045
```

Module 6: measure it and run it.

```sh
python -m doc_extract.evaluate --systems text,ocr,ocr_prepared,vision,vision_v1,combined
python -m doc_extract.budget --pages 300 --model-share 0.25
python -m doc_extract.pipeline run            # every document, results in out/results/
python -m doc_extract.pipeline regression     # the regression set (tests/regression/expected.json)
python -m doc_extract.pipeline status         # results made by an older version
python -m doc_extract.pipeline reprocess      # run those again
python -m doc_extract.pipeline delete D045    # delete what the pipeline made from one document
```

## A live vision-model call (optional)

To call a vision model yourself, set `VISION_BASE_URL`, `VISION_API_KEY` and `VISION_MODEL` (see
`.env.example`; any OpenAI-compatible endpoint whose model reads images), then add `--live`:
`python -m doc_extract.vision D036 --live`. It costs about one US cent per page. Your answer can differ
from the recorded one.

## Licence

MIT. The packages it uses have permissive licences (MIT, BSD or Apache 2.0).
