# Vision AI: See, Count and Inspect

The files for the Vision AI course of Nextia Learning.

| Folder or file | What it is |
|---|---|
| `data/` | The Larkfield image sets: catalogue photos, returned candles, pallet photos, customer photos, a replayed month. Read `data/dataset-card.md` first: it gives the licence and the source of every image. |
| `compare.py` | The comparison table helper that the notebooks use: the same scores, the same cost table, for every method. |
| `models/` | The model files of the image service: the returns inspector and a face detector. See `models/README.md`. |
| `snapshots/` | The `larkvision` project at the end of each module (`start`, `end-of-m02` ... `end-of-m08`). See `snapshots/README.md`. |
| `M01-L04-...` to `M08-L04-...` | Lesson notebooks: a learner notebook and a solution notebook for each. They open in Colab, Kaggle or Jupyter and download what they need. |
| `M09-L01-...` to `M09-L03-...` | The case studies' notebooks. Case studies 1 and 3 have their photos next to them (`visa-pcb.zip`, a changed copy of part of VisA, CC BY 4.0; `crowd.zip`, Open Images photos, CC BY 2.0 each by its author: see each `dataset.md`). Case study 2 downloads the Oxford-IIIT Pet photos from their own site (CC BY-SA 4.0); nothing of them is stored here. |
| `archives/` | The image sets as zip files, for the notebooks (the same files as `data/`). |
| `final/` | The final assignment: the task (`final/README.md`) and its images. |

Everything runs on a laptop CPU. You need no key, no graphics card and no money.

## Quick start

macOS and Linux:

```sh
cd snapshots/start
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
vision info
```

Windows (PowerShell):

```powershell
cd snapshots\start
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e . --no-deps
vision info
```

## What is real and what is made by code

- The catalogue photos are cut from open photos (Open Images, CC BY 2.0). The returned candles are photos of the VisA inspection set (CC BY 4.0). Each photo's author and source are in the manifests.
- The pallet photos are drawn by our code. The customer photos, the "new studio" light and the new camera are changes that our code made to real photos. The manifests mark all of them `synthetic: yes`.
- Some problems are planted on purpose: the course says so each time ("a problem we planted").
- The hidden test sets are not here. The course team keeps them, so that a final score is honest.
