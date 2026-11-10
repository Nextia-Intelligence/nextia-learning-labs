# larkfield-recs: the end of module 4 (*Neighbours and collaborative filtering*)

Larkfield's recommender, the project of the course *Recommendation and Personalisation: Show Each Person What Matters*. The `recs` command scores recommendation methods on Larkfield's shop log with the same time split and the same measures, so that you can compare them fairly.

The shop log is **synthetic**: our code made it with a model of customer behaviour. It is not real customer data.

## Set up

You need Python 3.12. This stage installs NumPy, pandas, SciPy and pytest. The course data is the `data` folder of this course's labs folder (`../../data` from here); the project finds it there, or set `LARKFIELD_DATA` to its path.

macOS and Linux:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e . --no-deps
```

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e . --no-deps
```

Check the setup: `recs check` prints `Setup check passed.` Run the tests: `python -m pytest -q`.

## Try

```sh
recs evaluate item-cf --by segment
recs similar P10020
recs explain C100123
```

Everything the project writes (runs, models, suggestion lists, deletion requests) goes to `outputs/`. `recs reset` deletes it and checks the data files.

Licence: MIT (see LICENSE).
