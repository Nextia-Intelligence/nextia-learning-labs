# Document and Multimodal AI

Files for the course [Document and Multimodal AI](https://learning.nextia-ai.com/courses/document-ai/).

| Folder | What it has |
|---|---|
| [`snapshots/`](snapshots) | The course project `doc-extract`: `start` (download it in the first lesson) and the project at the end of each module. Code MIT. |
| [`data/`](data) | The course's 65 documents (receipts as PDFs, scans and phone photos, a price list, a spreadsheet, two policies, a warranty claim and seven problem files) and their true values, `truth.jsonl`, with a [dataset card](data/dataset.md). All made up by the project's generator. CC0. |
| [`read-real-receipts/`](read-real-receipts) | Case study 1, [Read real receipts](https://learning.nextia-ai.com/courses/document-ai/m07/read-real-receipts/): the project `cord-receipts` as `starter.zip` (the parts you write are missing) and `finished.zip` (the whole project), and a fixed sample of 100 receipt photos from CORD v2 (NAVER CLOVA, CC BY 4.0) in `data/`, with a [dataset card](read-real-receipts/dataset.md). The project downloads the sample from this repository and checks its SHA-256. Code MIT. |
| [`public-report-table/`](public-report-table) | Case study 2, [Extract a table from a public report](https://learning.nextia-ai.com/courses/document-ai/m07/extract-a-table-from-a-public-report/): a notebook and its solution, `report_table.py`, the recorded vision-model answers, and two monthly *Crop Production* reports of the US Department of Agriculture (public domain) as PDF and CSV in `data/`, with a [dataset card](public-report-table/dataset.md). The notebook tries the agency's site first, then this copy, and checks the SHA-256 of every file. Code MIT. |

The case studies use real public documents, not Larkfield's, and need an internet connection for their setup steps.

Each snapshot makes the same documents itself (`python -m doc_extract.generate --check`). Use `data/`
only when `--check` says that your files differ: copy `documents/` and `truth.jsonl` into the
project's `data/` folder.

You need no account, no key and no money. The PDF text layer and OCR run on your computer's CPU, and
the vision model's answers were recorded by the course team: the project replays them. A live call
to a vision model with your own key is optional.

## Versions

Python 3.12 or later; pdfplumber 0.11.10, pypdf 6.20.0, pypdfium2 5.14.0, RapidOCR 3.10.0 on ONNX
Runtime 1.31.0, Pillow 12.3.0, openpyxl 3.1.5. The recorded vision answers came from one hosted
vision model; another model, or the same model later, can answer differently.

## Tested

Tested with Python 3.12 on macOS (Apple silicon): every snapshot, in a new virtual environment,
makes the documents, passes its lint and its tests, and the stage's first commands run. Windows and
Linux are not tested; the commands for them are in each snapshot's README.

The case-study notebook and its solution ran from a fresh start in a new virtual environment. The
case-study project ran from fresh copies of its starter and finished projects: its tests pass, its
notebook runs, and the commands on its page run.
