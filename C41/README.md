# Speech AI: the Larkfield calls and the IVR project

This folder belongs to the Speech AI course of Nextia Learning. It holds:

- `data/`: the Larkfield call set (synthetic: open text-to-speech voices read invented scripts). Read
  `data/dataset-card.md` first.
- `compare.py`: the normalisation guide, WER and CER with the alignment, the important-word errors and the
  comparison table. It needs only Python.
- `snapshots/`: the course project, `larkspeech` and its `speech` command, at the end of each module (`start`,
  `end-of-m02` ... `end-of-m09`). The last ones contain the Larkfield IVR and its test phone.
- one folder per notebook lesson.
- `M10-*`: the four case studies, each with its notebooks and its own sample of open, real recordings in
  `data/` (read its `dataset.md` for the source, the licence and the attribution).
- `final/`: the public data of the final assignment (40 French calls and 20 IVR calls on a new phone line, with
  no answers). Read `final/README.md` first.

## Start (macOS or Linux)

```sh
cd snapshots/start
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -e .
speech info
speech check
```

## Start (Windows PowerShell)

```powershell
cd snapshots\start
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -e .
speech info
speech check
```

`speech check` downloads Whisper tiny (about 75 MB) the first time, transcribes one call and prints its word error
rate and real-time factor. `speech reset` removes your outputs and checks every data file. You need no key, no
graphics card and no money.
