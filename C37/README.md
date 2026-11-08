# Recommendation and Personalisation: Show Each Person What Matters

Practice files for the course at [learning.nextia-ai.com/courses/recommendations/](https://learning.nextia-ai.com/courses/recommendations/).

| Path | What it is |
|---|---|
| `data/` | The Larkfield shop log: 2,994 products, 40,000 customers and 805,316 events (views, basket adds and orders) from 1 February 2025 to 5 July 2026, product embeddings, the simulated online test, and recorded language-model answers. Read [`data/dataset-card.md`](data/dataset-card.md). |
| `snapshots/start/` | The `larkfield-recs` project at the start of the course (Module 1): the `recs` command, the time split, the first measures and the popularity baseline. |
| `snapshots/end-of-m02/` … `end-of-m09/` | The same project at the end of each module. `end-of-m09` is the finished project: every method, the two-stage ranker, the business rules and the recommendation service. |
| `Mnn-Lnn-<slug>/` | The lesson notebooks, each with a solution notebook. Each one downloads what it needs, so you can open any lesson without the earlier ones. |

## Run the project on your computer

Python 3.12. Copy a snapshot folder (keep `data/` two folders up, or set `LARKFIELD_DATA` to its path), then in that folder:

```sh
python3.12 -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e . --no-deps
recs check                           # Setup check passed.
recs evaluate popular --quick
```

The `README.md` of each snapshot lists the commands of that stage. `recs reset` deletes everything the project wrote.

## Open a notebook

Open a lesson's notebook in Colab, Kaggle or VS Code and run it from the top. The first cell installs the packages. Every notebook runs on a laptop CPU in a few minutes, with no key and no graphics card.

The Larkfield shop log is synthetic: our code made Larkfield, its products, its customers and everything they did, with a model of customer behaviour. There are no real people in it. The online test in `data/online/` is simulated on that model, not run on real customers.
