# Snapshots: ticket-adapter at the start and at the end of each module

Each folder here is the `ticket-adapter` project of [Fine-Tuning and Adapting AI Models](https://learning.nextia-ai.com/courses/fine-tuning/). `start` is the project that you download in the lesson *Clarify the failure*. The others are the project after the last lesson of one module. If your project is broken or missing, copy the snapshot of the module that you finished last, and continue with the next lesson.

| Snapshot | Use it to start | What it has (new) | Tests |
|---|---|---|---|
| [`start`](start) | Module 1, lesson 1 | The evaluation cases of the evaluation course (271), `python -m adapt cases` and `show`. | 3 |
| [`end-of-m01`](end-of-m01) | Module 2 | The strict answer check (`answer.py`), the saved replies of the hosted model and of the small base model, the kinds of mistake (`failures.py`), scores and targets (`scoring.py`, `targets.toml`), the go/no-go memo. | 9 |
| [`end-of-m02`](end-of-m02) | Module 3 | The training tickets with their sources and permitted use (`data/sources.toml`), training examples (`records.py`), cleaning, splitting and the leak check (`prepare.py`), the prepared data, the exercise. | 17 |
| [`end-of-m03`](end-of-m03) | Module 4 | The model's small files (`model/`), parameter counts (`params.py`), memory estimates (`memory.py`), the method choice. | 21 |
| [`end-of-m04`](end-of-m04) | Module 5 | PyTorch, `transformers` and `peft`; the run configurations (`configs/`), training with checkpoints and resume (`train.py`), the three recorded runs (`runs/`). | 27 (+1 that needs the model) |
| [`end-of-m05`](end-of-m05) | Module 6 | The local systems (`predict.py`), the saved replies of every system, regressions, costs, the result memo. | 34 (+2) |
| [`end-of-m06`](end-of-m06) | The final assignment | The bundle and its checks (`bundle.py`), the lifecycle plan, the full README. The course-end project. | 36 (+3) |

Each snapshot has only what the lessons' guided practice makes. It does not have the answers to the "Your turn" tasks. From `end-of-m04`, every snapshot has the course's recorded runs, so you never need to train.

## What a snapshot does not have

- The virtual environment `.venv`. Make it again when you set up (see the snapshot's README).
- The base model's weights. From Module 4, `python -m adapt download` gets them (about 270 MB). The tests that need them run with `python -m pytest -m model`.
- Checkpoints and `bundle/`: you make them when you train or package.

## Use a snapshot

The steps use `end-of-m03` as an example. Use the name of your snapshot.

1. Get the files. If you have Git, clone this repository once, in `~/projects`:

   ```sh
   cd ~/projects
   git clone https://github.com/Nextia-Intelligence/nextia-learning-labs.git
   ```

   If you already have the clone, get the newest files with `git -C nextia-learning-labs pull`. Without Git, download [the ZIP file of this repository](https://github.com/Nextia-Intelligence/nextia-learning-labs/archive/refs/heads/main.zip), and unzip it in `~/projects`. Its folder is `nextia-learning-labs-main`.
2. Keep your own project. If `~/projects/ticket-adapter` exists, rename it:

   ```sh
   mv ticket-adapter ticket-adapter-old     # Windows: Rename-Item ticket-adapter ticket-adapter-old
   ```

3. Copy the snapshot:

   ```sh
   cp -r nextia-learning-labs/C12/snapshots/end-of-m03 ticket-adapter     # Windows: Copy-Item -Recurse nextia-learning-labs\C12\snapshots\end-of-m03 ticket-adapter
   ```

4. Make the virtual environment and install the packages, as in the snapshot's README.
5. Check it: `python -m pytest`. The last line says how many tests passed; it must match the table above.
