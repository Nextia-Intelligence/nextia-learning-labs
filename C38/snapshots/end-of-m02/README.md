# larkfield-search — End of Module 2: measure relevance

Larkfield's product search: the project of the Search and Ranking course. You run it with the `search` command. The catalogue and the judgments are derived from WANDS, the Wayfair ANnotation DataSet (MIT). The query log, prices, stock and sale flags are synthetic, made by our code.

## What this stage has

- the course data reader and the comparison helper (`compare.py`: NDCG, recall, MRR, intervals)
- two indexes: SQLite FTS5 (Larkfield's search today: every word must match) and BM25
- commands: `info`, `index`, `query`, `eval`, `log`, `check`, `reset`
- relevance judgments: `search judge sample`, `search judge agree`, `search judge llm`
- judging guidelines (`docs/judging-guidelines.md`)
- `search compare A B`: is B really better than A? (the difference with its 95% interval, by slice)

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
```

Every command writes only to `outputs/` (the index, trained models). `search reset` deletes that folder and checks the data. Run the tests with `pytest` (they use a tiny fake data folder, no download).

## Licence

The code is MIT (see `LICENSE`). The data has its own dataset card in `data/`.
