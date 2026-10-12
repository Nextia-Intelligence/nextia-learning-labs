# Fine-Tuning and Adapting AI Models

Files for the course [Fine-Tuning and Adapting AI Models](https://learning.nextia-ai.com/courses/fine-tuning/).

| Folder | What it has |
|---|---|
| [`data/`](data) | The training tickets (made up, CC0) with their needs-a-person labels and known wrong labels, the evaluation cases of the evaluation course, Grace's policy, the [dataset card](data/dataset.md) and the script that builds them. |
| [`runs/`](runs) | The course's recorded training runs and every saved reply, so that every lesson works without training: logs and loss curves, the LoRA adapters, the predictions of each system on the evaluation cases, the answers to the general questions. |
| [`snapshots/`](snapshots) | The course project `ticket-adapter`: `start` (download it in the lesson *Clarify the failure*) and the project at the end of each module. Code MIT; data and recorded outputs CC0; the model's small files Apache-2.0. |
| [`should-this-team-fine-tune/`](should-this-team-fine-tune) | The case study [Should this team fine-tune?](https://learning.nextia-ai.com/courses/fine-tuning/m07/should-this-team-fine-tune/): a notebook and its solution, the recorded replies of every system and the two recorded LoRA runs with their adapters, and a [dataset card](should-this-team-fine-tune/dataset.md). The notebook downloads CLINC150 (CC BY 3.0) from its publisher at one fixed version. Code MIT; for the data and what was made from it, see the dataset card. |

You need no account, no GPU and no money. Modules 1 to 3 need only Python. From Module 4, the project
installs PyTorch (CPU) and downloads the base model SmolLM2-135M-Instruct (about 270 MB, Apache-2.0).
Training again is optional: one run takes a few minutes on a laptop processor.

The case study uses real public data, not Larkfield's. Its notebook needs an internet connection for its setup step, and it checks the SHA-256 of every file that it downloads.
