# larkfield-search — End of Module 8: run search in production (the course-end project)

Larkfield's product search: the project of the Search and Ranking course. You run it with the `search` command. The catalogue and the judgments are derived from WANDS, the Wayfair ANnotation DataSet (MIT). The query log, prices, stock and sale flags are synthetic, made by our code.

## What this stage has

- the course data reader and the comparison helper (`compare.py`: NDCG, recall, MRR, intervals)
- two indexes: SQLite FTS5 (Larkfield's search today: every word must match) and BM25
- commands: `info`, `index`, `query`, `eval`, `log`, `check`, `reset`
- relevance judgments: `search judge sample`, `search judge agree`, `search judge llm`
- judging guidelines (`docs/judging-guidelines.md`)
- `search compare A B`: is B really better than A? (the difference with its 95% interval, by slice)
- BM25 per field with weights (`bm25-title`, `bm25-fields`) and `search explain` (each part of a score)
- an exact-match rule for product codes (`bm25-fields+codes`)
- normalising and stemming in English and French, spelling correction, synonym rules, the recorded rewrites of a language model, and price and class detection (runs `bm25-norm` ... `bm25-norm+spell+syn+detect`, `llm-rewrite`)
- dense retrieval with shipped embeddings (`dense`) and two hybrid searches (`hybrid-rrf`, `hybrid-blend`)
- a cross-encoder on the top candidates (`rerank-ce`, recorded scores)
- learning to rank with LightGBM (`ltr`, `ltr-clicks`, `ltr-clicks-ipw`), `search ltr train`
- position bias in the log: `search clicks bias`
- autocomplete (`search suggest`), facets (`search facets`), business rules and fallbacks (runs `ltr+sale-first`, `ltr+stock-last`, `ltr+explore`, `current+fallback`), and the search page (`search serve`)
- latency and cost of each stage (`search bench`)
- interleaving and A/B tests, simulated (`search interleave`)

## Set up

You need Python 3.12 and the course data folder `data/` next to the `snapshots/` folder (the labs repository has it there), or set `LARKFIELD_DATA` to its path.

macOS and Linux:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
search check
```

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e . --no-deps
search check
```

On Linux, install the CPU version of PyTorch first, so pip does not download the large GPU version:

```sh
pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
```

On macOS, LightGBM needs the OpenMP library: `brew install libomp` (Homebrew). If `search ltr train` says `Library not loaded: libomp.dylib`, this is the fix.

The first time you search with a new query by meaning (`dense`, `hybrid-*`) or re-rank a new pair, the project downloads the model from Hugging Face (the bi-encoder about 200 MB, the cross-encoder about 600 MB). The queries of the course already have their embeddings and scores in `data/`, so the lessons do not wait.

`search check` ends with `Setup check passed.` If it does not, read its last line: a missing or changed data file means you should download the data again.

## Commands

```sh
search info
search index
search query "garden hose"
search eval --run bm25
search log --top 10
search check
search reset
search judge sample
search judge agree
search judge llm
search compare current bm25 --by band
search explain "emma headboard" LK-97580
search eval --run bm25-fields+codes
search compare bm25 bm25-fields+codes --by source
search query "outdor cushion" --run bm25-norm+spell
search eval --run bm25-norm+spell+syn --by source
search compare bm25-norm bm25-norm+spell --by source
search eval --run hybrid-rrf --by qtype
search query "seat for the garden" --run dense
search eval --run rerank-ce
search ltr train
search eval --run ltr
search clicks bias
search suggest gar
search facets "outdoor cushion"
search eval --run ltr+sale-first
search serve
search bench --queries 10
search interleave hybrid-rrf ltr --seeds 2
```

Every command writes only to `outputs/` (the index, trained models). `search reset` deletes that folder and checks the data. Run the tests with `pytest` (they use a tiny fake data folder, no download).

## Licence

The code is MIT (see `LICENSE`). The data has its own dataset card in `data/`.
