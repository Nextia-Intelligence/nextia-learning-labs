# The course project at each stage

`larkroute` is Larkfield's message router: the `route` command and, at the end, a small routing service. Each folder is the project at one point of the course. Copy the folder of the stage you start from, and follow the `README.md` inside it.

| Folder | The project after | What it adds |
|---|---|---|
| `start/` | *Meet the inbox* | The data, the cost table, the comparison table's columns, the keyword rules and TF-IDF with logistic regression: `route info`, `route compare --quick`, `route reset`. |
| `end-of-m02/` | Labels you can trust | `route agreement` (agreement and Cohen's kappa). |
| `end-of-m03/` | Baselines: rules and classical models | Naive Bayes, a linear SVM, strong rules with a model, and `route explain`. |
| `end-of-m06/` | Decision models, cascades and distillation | The recorded methods in `route compare` (embeddings, the fine-tuned encoder, zero-shot models, hosted and local LLMs), `route llm` and `route cascade`. |
| `end-of-m08/` | Confidence and people in the loop | `route calibration`, `route zones` and `route corrections`. |
| `end-of-m09/` | Run it in production | Model versions, the routing service (FastAPI), `route train`, `route serve`, `route drift` and `route release`. |

Modules 4, 5 and 7 are notebook lessons: they do not change the project. Their results come into the project as recorded files in `data/` at `end-of-m06`.

Each folder needs Python 3.12 and the data: run `python get_data.py` in it. Run `python -m pytest -q` to check it. The number of tests grows with each stage.

Tested on macOS (Apple silicon). The commands for Windows (PowerShell) and Linux are in each `README.md`.
