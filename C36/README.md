# Text Classification and Routing: Send Each Message to the Right Place

Practice files for the course at [learning.nextia-ai.com/courses/text-routing/](https://learning.nextia-ai.com/courses/text-routing/).

| Path | What it is |
|---|---|
| `data/` | The Larkfield inbox: 10,000 support messages in English and French with their routes (train, validation and test), the launch month (2,000 messages with no labels), the labelling guidelines, two people's labels on 800 messages, the old system's noisy labels, agents' queue moves, the cost table, and the recorded model answers. Read [`data/dataset-card.md`](data/dataset-card.md) and [`data/guidelines.md`](data/guidelines.md). |
| `routing.py` | The course's helper for notebooks: the cost table, the columns of the comparison table, and the reliability table. |
| `Mnn-Lnn-<slug>/` | The lesson notebooks, each with a solution notebook. Each one downloads what it needs, so you can open any lesson without the earlier ones. |
| `models/finetuned-encoder/` | The ready fine-tuned encoder, for learners who skip the training on their own computer. |
| `final/` | The final assignment: March 2026 with labels (a new marketplace channel), 100 messages labelled twice, and April 2026 with no labels to replay. Read [`final/README.md`](final/README.md). |
| `snapshots/` | The course project `larkroute` (the `route` command) at each stage of the course, from `start` to `end-of-m09`. |

## Open a notebook

Open a lesson's notebook in Colab, Kaggle or VS Code and run it from the top. The first cells install the packages (pandas 3.1.1, scikit-learn 1.9.1 and, where a lesson needs them, cleanlab 2.9.0, sentence-transformers 6.2.0 or transformers 5.22.2 with PyTorch 2.15.0 on the CPU), download the data and check its checksums. Every notebook runs on a laptop CPU in a few minutes.

## Run the project on your computer

Python 3.12. Copy one folder of `snapshots/` (start with `start/`), then in that folder:

```sh
python -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python get_data.py
python -m pytest -q
route compare --quick
```

The `README.md` of each folder lists its commands.

The Larkfield inbox is synthetic: Larkfield, its products and its customers are made up, and there are no real people. The answers of hosted models were recorded once: you need no key and no account.
