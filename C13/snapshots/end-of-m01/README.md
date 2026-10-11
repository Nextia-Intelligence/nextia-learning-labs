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

## Licence

MIT. The packages it uses have permissive licences (MIT, BSD or Apache 2.0).
