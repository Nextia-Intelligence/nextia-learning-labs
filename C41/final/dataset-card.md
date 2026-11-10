# Dataset card: the Larkfield calls of the new region (synthetic)

Used by: the final assignment of the Speech AI course (https://learning.nextia-ai.com/courses/speech/final-assignment/)

| Field | Value |
|---|---|
| Source | Made by the course team's code: invented scripts read by open text-to-speech voices |
| Publisher / creator | Nextia Learning |
| Licence | CC BY 4.0 (calls and files in this folder), with the attribution of the voices below |
| Attribution text | Larkfield synthetic calls, Nextia Learning (CC BY 4.0). Voices: Piper `fr_FR-siwis-medium` and Kokoro-82M `ff_siwis` (both learned from the SIWIS French Speech Synthesis Database, CC BY 4.0), Piper `fr_FR-gilles-low` (French Single Speaker Speech Dataset, CC0). |
| Version or access date | The course's call set, version 1 |
| File used | All files are in this folder |
| SHA-256 | `SHA256SUMS` lists every file |
| Size | 40 conversations (`calls/calls.jsonl`, 6 columns) and 20 IVR test calls (`ivr/calls.jsonl`), see `README.md` for the size |

## What one row means

In `calls/calls.jsonl`, one row is one phone conversation between a Larkfield agent and a caller from the new
French-speaking region, with its recording in `calls/phone/`. In `ivr/calls.jsonl`, one row is one test call to the
IVR: the caller's turns only, one audio file each. There is no target column: the assignment asks you to make the
labels that you need.

## Why this dataset

It is the course's call set, moved to a new situation: a new language mix (all French), a new phone line and new
product names. The same methods meet new conditions, so you must measure each choice again instead of copying it.
Real customer calls are never used for practice: they hold voices, names and sometimes card numbers, and the people
did not agree to it.

## Changes we made

- The scripts are made by the same code as the course's calls (templates for the agent, the numbers, dates and
  promises). The callers' own sentences were written by a hosted language model and checked by code.
- The line: each side is band-limited to 300-3,400 Hz, coded with G.726 at 16 kbit/s, and 3% of the 20 ms packets
  are dropped at random (they become silence). Then the audio is stored as 8 kHz G.711 mu-law.
- Background talk is other synthetic voices; street noise is made by code.
- The IDs are new. They do not show the order in which the calls were made.
- Practice problems were planted, as in the course's calls. The course page names the kinds; the dataset does not
  mark which call has which.

## Limitations and cautions

- **Synthetic voices.** They are cleaner and more regular than people: no real hesitations, no talking over each
  other, no real regional accents. Errors on real calls are higher.
- **Few French voices.** Only three voices speak French, and two of them learned from the same speaker. Part of the
  French error rate comes from the voices' own pronunciation, not from the recogniser. Speaker variety is low.
- **Small.** 40 conversations and 20 IVR calls. One word error moves a French WER by a few hundredths of a point on
  the whole set, and much more on a slice. Give the number of calls and words with every result.
- **Same patterns as the course.** The calls follow the course's scripts. A method tuned on them can look better
  than it would be on real calls.
