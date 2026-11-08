# Larkfield speech tools: end of Module 8

This is the course project of the Speech AI course at the end of Module 8 (From IVR to voice agent). The package is `larkspeech`; the command
is `speech`. Every Larkfield call is synthetic (open text-to-speech voices read invented scripts).

## What this stage adds

The voice agent replayed from recordings, its latency budget, and the IVR, the agent and a hybrid on the same calls (`agent.py`).

Commands so far: `speech info`, `speech inspect`, `speech check`, `speech reset`, `speech wer`, `speech score`, `speech vad`, `speech transcribe`, `speech diarize`, `speech reason`, `speech compliance`, `speech ivr serve`, `speech ivr replay`, `speech agent budget`, `speech agent compare`.

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

## The test phone

`speech ivr serve` starts the IVR on http://127.0.0.1:8041/. Open the page, press **Call**, allow the microphone
and talk to it, or use the keypad. Wear headphones. Your voice stays on your computer. Stop the server with Ctrl+C.

Optional paths (not tested by the course team, and they cost money or need an account): connect the same app to a
real phone number with a provider's media stream (for example Twilio Media Streams), or wire it to Asterisk in a
container with a softphone. The course page explains both.

Licence: MIT (this code). The voices and models have their own licences: see `../../data/voices.json` and the
course page.
