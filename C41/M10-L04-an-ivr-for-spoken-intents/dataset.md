# Dataset card: MInDS-14 (four varieties)

Used by: the case study *An IVR for spoken intents* (Speech AI course), `an-ivr-for-spoken-intents.ipynb` and `an-ivr-for-spoken-intents-solution.ipynb`

| Field | Value |
|---|---|
| Source | https://huggingface.co/datasets/PolyAI/minds14 (paper: https://arxiv.org/abs/2104.08524) |
| Publisher / creator | PolyAI Limited (Gerz, Su, Kusztos, Mondal, Lis, Singhal, Mrkšić, Wen, Vulić) |
| Licence | CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ (the dataset page's licence tag; the card says "Creative Commons license (CC-BY)") |
| Attribution text | MInDS-14, PolyAI (Gerz et al., 2021, arXiv 2104.08524), CC BY 4.0. Clips converted from mu-law to 16-bit PCM WAV by Nextia Learning; transcripts and intents are the dataset's own; Whisper and LLM outputs by Nextia Learning. |
| Version or access date | Dataset repository commit `40ce77cb32a384e4d50a568e1ec39ac804019d33`; configs `en-US`, `en-GB`, `en-AU`, `fr-FR` (`train` split, the only one) |
| File used | `<variety>/train-00000-of-00001.parquet` (4 files, 138 MB); kept in `data/`: a fixed sample (below), not the parquet files |
| SHA-256 | en-US `37004471dc896ce20771b3fdda0ee8fb33ec7a030fb4e2fd047c561ec0a1ee30`, en-GB `52c988dc66991be64109bb7043fd3acb8c00a7cfc1006670ee0b3906868a9b00`, en-AU `74476455327528992aa23a321ca3f1de3037c863a7d76b56e2a05df19cba4bab`, fr-FR `84b20ae271f627474ee3f8140c5d0b64a8f09a8c3d4f4ba8c2a6ee0dec8c295c`; the files in `data/` are in `data/SHA256SUMS` |
| Size | 2,348 requests (en-US 563, en-GB 592, en-AU 654, fr-FR 539), 5.47 hours of 8 kHz audio |

## What one row means

One spoken request to a bank's phone line by one crowd worker, a native speaker of the variety. The target is the
**intent**: one of 14 (abroad, address, app_error, atm_limit, balance, business_loan, card_issues, cash_deposit,
direct_debit, freeze, high_value_payment, joint_account, latest_transactions, pay_bill).

## Why this dataset

Real voices, many intents, phone audio, English and French, and a licence that allows reuse with attribution. Compared
with SLURP (audio CC BY-NC 4.0), Speech-MASSIVE (CC BY-NC-SA 4.0), Fluent Speech Commands (non-commercial licence)
and BANKING77 (text only); see the course's research notes.

## Changes we made

- `clips.jsonl`: one line per request with our ID (`<variety>-<row number>`), variety, language, intent name, the
  dataset's `transcription` (as `transcript`) and `english_transcription` (as `english`), and the length in seconds.
  No audio except the 12 clips below.
- `audio/*.wav`: 12 requests of the part kept apart as new input, converted from 8 kHz mu-law to 8 kHz 16-bit PCM WAV
  (nothing else changed).
- `recorded/`: our outputs. Whisper base and Whisper small transcripts of every request (faster-whisper 1.2.1, int8,
  CPU, beam 1), and Azure chat-small's intent answers from the Whisper base, Whisper small and dataset transcripts
  (text only; no audio was sent).

## Limitations and cautions

- **The transcripts are machine-made** (Google's recogniser, paper §4): there is no human reference, so a comparison
  with them is a disagreement rate, not a word error rate.
- **Prompted requests:** each worker saw the intent, a description and three examples, then spoke. Real callers are
  less tidy. One sentence per request; no dialogue.
- **No speaker IDs, gender or age.** One worker may have many requests, so random splits can put one voice on both
  sides. The only group is the language variety.
- Some labels overlap (for example "freeze my card" against card problems).
- Real people's voices: use short clips with their transcript, never try to identify a speaker, and do not clone voices.
