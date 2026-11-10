# Experiments and Causal Impact: Did Our Change Work?

Practice files for the course at [learning.nextia-ai.com/courses/experiments/](https://learning.nextia-ai.com/courses/experiments/).

| Path | What it is |
|---|---|
| `snapshots/` | The course project `larkfield-experiments` at each stage: `sim`, a traffic simulator that knows the true effect of every change, and `xp`, the analysis tool. Start with `snapshots/start/`. Read [`snapshots/README.md`](snapshots/README.md). |
| `data/` | The simulator's runs that the lesson notebooks read (made with the default seeds), and the recorded answers of the support assistant. Read [`data/dataset.md`](data/dataset.md). |
| `Mnn-Lnn-<slug>/` | The lesson notebooks, each with a solution notebook. Each one downloads what it needs, so you can open any lesson without the earlier ones. |
| `final-assignment/` | The data of the final assignment: a new change, its test, the logs from before the test, and next month's customers. |

## Run the project on your computer

Python 3.12. Copy `snapshots/start/` (or the snapshot of the module you are on), then in that folder:

```sh
python3.12 -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -m pytest -q
sim run --scenario email
xp analyse
xp check
```

The `README.md` of each snapshot lists its commands.

## Open a notebook

Open a lesson's notebook in Colab, Kaggle or VS Code and run it from the top. The first cell installs the packages (pandas 3.1.1, SciPy 1.15.3, statsmodels 0.15.0 and matplotlib 3.11.2); the next one downloads the data and checks its checksums. Every notebook runs on a laptop CPU in a few minutes.

All Larkfield data is synthetic: Larkfield, its customers and its changes are made up, and there are no real people. The support assistant's answers were recorded once from a language model and are replayed, so you need no key.
