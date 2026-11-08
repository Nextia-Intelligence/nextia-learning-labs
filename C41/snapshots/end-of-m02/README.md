# Larkfield speech tools: end of Module 2

This is the course project of the Speech AI course at the end of Module 2 (Measure before you choose). The package is `larkspeech`; the command
is `speech`. Every Larkfield call is synthetic (open text-to-speech voices read invented scripts).

## What this stage adds

WER and CER with the alignment, the normalisation guide, and scores by slice with the important words (`scoring.py`).

Commands so far: `speech info`, `speech inspect`, `speech check`, `speech reset`, `speech wer`, `speech score`.

## Start (macOS or Linux)

```sh
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -e .
speech info
```

## Start (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -e .
speech info
```

The data is in `../../data` (the labs folder of the course); set `LARKSPEECH_DATA` to use another folder. Models
are downloaded the first time a command needs them (Whisper from Hugging Face; voices and the speaker model with a
SHA-256 check) into `models/` and the Hugging Face cache. `speech reset` removes `outputs/` and checks the data.

Run the tests with `pytest -q`. They use a tiny fake data folder and need no download.

Licence: MIT (this code). The voices and models have their own licences: see `../../data/voices.json` and the
course page.
