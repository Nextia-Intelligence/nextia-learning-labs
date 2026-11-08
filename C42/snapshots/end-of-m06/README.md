# larkvision: Larkfield's image tools (end of Module 6)

This is the project of the Vision AI course at this point of the course. The `vision` command compares vision methods on the same Larkfield photos.

## Set up

You need Python 3.12. The data folder of the course (`data/`, next to `snapshots/`) must be there.
The commands find `../../data` by themselves. To use another folder, set `LARKVISION_DATA`.

macOS and Linux:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
python -m pytest -q
vision info
```

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e . --no-deps
python -m pytest -q
vision info
```

## Commands

- `vision info`: what is in the data folder, with the licences and the cost table.
- `vision compare --task catalogue`: the comparison table (tasks: catalogue, inspect, count, match, attributes).
- `vision reset`: remove outputs/ and review/, and check every data file.
- `vision baseline --method histogram`: a colour histogram with nearest neighbours.
- `vision baseline --method hog`: HOG features with a logistic regression.
- `vision probe --embeddings clip --per-class 20`: a linear probe on embeddings with 20 photos per class.
- `vision probe --embeddings clip --balanced`: all labels, every class with the same weight.
- `vision labels --embeddings dinov2 --score`: training photos whose label looks wrong.
- `vision count --method finetuned-40 --score 0.5`: count boxes from a detector's recorded boxes.
- `vision count --method owlv2 --score 0.075 --nms 0.3`: the open-vocabulary detector.
- `vision count --method label-rule`: count the white labels: a rule, no model.
- `vision masks`: the area of each damage, from its mask, with a tea light for scale.
- `vision zones --list`: the recorded anomaly scores.
- `vision zones --method small_patchcore --budget 100`: pass, check and fail lines for 100 checks a day.

Your own runs go to `outputs/table.json`; `vision compare` shows them next to the course's rows with "(yours)". `vision reset` removes them.

## What is real and what is recorded

- The photos are open photos (each with its licence and author in the manifests) or images drawn and changed by our code (marked `synthetic` in the manifests). The hidden test sets are not in this folder.
- Embeddings, detector boxes, anomaly scores and vision-language answers were made once by the course team with pinned models and saved in `data/`. The commands read these files, so they run in seconds, with no model download and no key.

## Licence

The code is MIT (see `LICENSE`). The data and model files have their own licences: see the dataset card in the data folder.
