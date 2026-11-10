# Speech AI: the final assignment's calls

Larkfield opens a French-language phone line in a new region. The line comes from a new phone provider, and the
region sells four new products. This folder holds the calls of that line, for the final assignment of the Speech
AI course. The task is on the course page: https://learning.nextia-ai.com/courses/speech/final-assignment/

**Every call is synthetic.** Open text-to-speech voices read invented scripts. Larkfield is an invented shop. No
real customer and no real person's voice is in this folder. Read `dataset-card.md` before you trust a number.

## What is here

| File or folder | What |
|---|---|
| `calls/calls.jsonl` | 40 conversations between a Larkfield agent and a caller, one line each: `call_id` (`N-001` to `N-040`), `split` (always `final`), `language` (always `fr`), `line` (always `new_provider`), `channels` (2: agent on channel 1, caller on channel 2; 1: both on one channel), `duration` (seconds). |
| `calls/phone/N-*.wav` | The 40 recordings, as the phone system stores them: 8 kHz, G.711 mu-law, stereo or mono. |
| `ivr/calls.jsonl` | 20 test calls to the IVR (`NI-01` to `NI-20`), the caller's side only: `call_id`, `split`, `language`, `line`, and `inputs` (one file per caller turn, with its length in seconds). |
| `ivr/NI-*/NN.wav` | One file per caller turn: speech, keypad tones or silence, 8 kHz mu-law. Play them in order: turn 01 answers the IVR's first prompt, turn 02 its second prompt, and so on. |
| `orders.json` | The new region's order system: 60 orders. Each has a 6-digit number that starts with 8 or 9 (the last digit is a check digit), the product, the status, the date and whether it can be returned. |
| `products.json` | The four new product names. Callers say them in English inside French sentences. |
| `costs.json` | The course's cost assumptions (the same file as in `../data/`). |
| `SHA256SUMS` | A checksum of every file. |

## What is not here

No labels. There is no reference transcript, no call reason, no summary, no promise, no recording-notice label, no
speaker turn and no expected IVR outcome. Making the labels that you need is part of the assignment. The course
team keeps its own labels and a hidden copy of the answers. Nobody chooses a method with them.

## The new line

Malik, Larkfield's telephony engineer, says this about the new provider: it uses the G.726 codec at 16 kbit/s, and
it loses up to about 3% of the 20 ms audio packets on the way. A lost packet is 20 ms of silence in the recording.

## Use it with the course project

Keep `larkspeech` and `nextia-learning-labs` side by side, as in the course. This folder is `final/`, next to the
course's `data/` folder. Give its path to the project with `--data` (or with the `LARKSPEECH_DATA` environment
variable), and check the files first:

```sh
cd larkspeech
. .venv/bin/activate
F=<the path of this folder>
(cd "$F" && shasum -a 256 -c SHA256SUMS | grep -vc ': OK$')     # prints 0
speech --data "$F" info
```

On Windows (PowerShell): `.venv\Scripts\Activate.ps1`, then `$F = "<the path of this folder>"` and
`speech --data $F info`. The course page gives the exact paths.

Commands that score against labels (`speech score`, `speech transcribe`'s WER line, `speech ivr replay`'s pass
column) need the labels that you make. The course page shows how.
