# Snapshots: doc-extract at the start and at the end of each module

Each folder here is the `doc-extract` project of [Document and Multimodal AI](https://learning.nextia-ai.com/courses/document-ai/). `start` is the project that you download in the first lesson. The others are the project after the last lesson of one module. If your project is broken or missing, copy the snapshot of the module that you finished last, and continue with the next lesson.

| Snapshot | Use it to start | What it has (new) | Tests |
|---|---|---|---|
| [`start`](start) | Module 1 | The document generator (`python -m doc_extract.generate`), the list of documents and their true values, `show`. | 9 |
| [`end-of-m01`](end-of-m01) | Module 2 | `route` (the format and the route of every page), the PDF text layer with boxes, reading order on two columns, the extraction contract. | 40 |
| [`end-of-m02`](end-of-m02) | Module 3 | Intake checks, OCR, the rules that fill the contract, the recorded vision-model answers, `compare` (three paths), image preparation. | 63 |
| [`end-of-m03`](end-of-m03) | Module 4 | Sections and footnotes, the table over two pages, the spreadsheet, the evidence of every value (`provenance`). | 77 |
| [`end-of-m04`](end-of-m04) | Module 5 | More recorded answers (crops, smaller pictures, a second pass), `combine` (rules and model), `uncertainty`. | 84 |
| [`end-of-m05`](end-of-m05) | Module 6 | Business validation, the review queue and its threshold, corrections that keep the original. | 98 |
| [`end-of-m06`](end-of-m06) | The final assignment | Field-level evaluation, the budget, the whole pipeline with versions, deletion and a regression set. The course-end project. | 107 |

Each snapshot has only what the lessons' guided practice makes. It does not have the answers to the "Your turn" tasks.

## What a snapshot does not have

- The virtual environment `.venv`.
- The documents: `python -m doc_extract.generate --check` makes them in `data/` (about 10 seconds). If it says that some files differ, copy `documents/` and `truth.jsonl` from [`../data`](../data) into the project's `data/` folder.
- `out/`: everything the commands write (the OCR cache, pictures, results, the review database). Delete `out/` to start again.

## Use a snapshot

The steps use `end-of-m03` as an example. Use the name of your snapshot.

1. Get the files. If you have Git, clone this repository once, in `~/projects`:

   ```sh
   cd ~/projects
   git clone https://github.com/usmanahmed99/nextia-learning-labs.git
   ```

   If you already have the clone, get the newest files with `git -C nextia-learning-labs pull`. Without Git, download [the ZIP file of this repository](https://github.com/usmanahmed99/nextia-learning-labs/archive/refs/heads/main.zip), and unzip it in `~/projects`. Its folder is `nextia-learning-labs-main`.
2. Keep your own project. If `~/projects/doc-extract` exists, rename it:

   ```sh
   mv doc-extract doc-extract-old     # Windows: Rename-Item doc-extract doc-extract-old
   ```

3. Copy the snapshot into a new `doc-extract` folder:

   ```sh
   cp -R nextia-learning-labs/C13/snapshots/end-of-m03 doc-extract
   ```

   On Windows, in PowerShell: `Copy-Item -Recurse nextia-learning-labs\C13\snapshots\end-of-m03 doc-extract`.
4. Make the virtual environment, the documents, and run the tests:

   ```sh
   cd doc-extract
   python3 -m venv .venv
   source .venv/bin/activate              # Windows: py -m venv .venv, then .venv\Scripts\Activate.ps1
   python -m pip install -r requirements-dev.txt
   python -m doc_extract.generate --check
   python -m pytest -q
   ```

   `end-of-m03` gives `77 passed`.

## Tested

Every snapshot was checked with Python 3.12 on macOS (Apple silicon), in a new virtual environment: it makes the documents, passes its lint and its tests, and the stage's first commands run. Windows and Linux are not tested.
