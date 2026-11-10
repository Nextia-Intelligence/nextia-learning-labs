# Dataset card: FLEURS, English and French (a sample)

Used by: case study *Choose a recogniser for two languages* (Speech AI course), `choose-a-recogniser-for-two-languages.ipynb`

| Field | Value |
|---|---|
| Source | https://huggingface.co/datasets/google/fleurs (revision `70bb2e84b976b7e960aa89f1c648e09c59f894dd`) |
| Publisher / creator | Google: Conneau, Ma, Khanuja, Zhang, Axelrod, Dalmia, Riesa, Rivera and Bapna, "FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech", 2022, https://arxiv.org/abs/2205.12446 |
| Licence | CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ (the dataset page's licence tag `cc-by-4.0`) |
| Attribution text | "FLEURS" by Google (Conneau et al., 2022), CC BY 4.0, https://huggingface.co/datasets/google/fleurs. Sample and FLAC conversion by Nextia Learning. |
| Version or access date | revision `70bb2e84b976b7e960aa89f1c648e09c59f894dd`, downloaded 2026-11-08 |
| File used | `data/audio/*.flac` (23 clips) kept in `data/`: yes (CC BY 4.0 allows it). The sentence text is downloaded from FLEURS itself (`en_us/test.tsv`, `fr_fr/test.tsv`, `en_us/dev.tsv`, `fr_fr/dev.tsv`): not kept here. |
| SHA-256 | every file in `data/SHA256SUMS`; the FLEURS text files: `en_us/test.tsv` `74c046239374deeb60fa63f258f907388093a32bcaa3140965f70ef05c79f7ca`, `fr_fr/test.tsv` `5d06d338b242e00786fcf12c4c92008b9f399d5a5c872c91dca90572e7869c0d`, `en_us/dev.tsv` `9d57ee7e91e9d4c92edb39f6bbea668ef8dc2a3ff96eb510d5580b2ad05d17ec`, `fr_fr/dev.tsv` `3e0b792358c1cb4a426fe1c18fc1571d5406b390d738a2ed1bfd3c8b9d28de44` |
| Size | 262 English and 230 French recordings in the sample (44.2 and 38.6 minutes of audio, not included), 20 new recordings (included), 2.9 MB in `data/` |

## What one row means

One row of `data/recordings.json` is one recording: one volunteer reading one sentence aloud, at 16 kHz. It gives the language, the sentence number, the FLEURS file name, the speaker's gender as FLEURS records it (female or male), and the length. The target is the sentence text (from FLEURS's `test.tsv`); a recogniser's job is to write it.

## Why this dataset

Real speech (the course's own calls are synthetic), the same sentences in English and French, and a gender label for every recording. In the test split, 131 English and 115 French sentences were read by both a woman and a man: our sample keeps exactly those, so the gender comparison uses the same sentences. Compared with Mozilla Common Voice (CC0 data, but downloads now need an account on Mozilla's platform), VoxPopuli (licence tags CC0 and "other"; parliament speeches) and Multilingual LibriSpeech (audiobooks; no English part of its own).

## Changes we made

- Sample: in each language, every test sentence read by both genders, with one recording of each gender (a fixed random choice when there were two). 20 recordings of the validation split (5 per gender and language) as new input.
- Audio: stored as 16-bit FLAC (FLEURS ships 32-bit float WAV). Only the 3 clips to listen to and the 20 new recordings are included; the sample's audio is not (the recorded transcripts are).
- `data/transcripts/`: our recorded transcripts of Vosk small and Whisper tiny, base, small (and medium on the first 25 sentences per language; small without the language), made on an Apple M4 laptop with 4 CPU threads.

## Limitations and cautions

- Read sentences in a quiet room: easier than spontaneous speech, phone lines or noisy places. Not a test of any one company's speakers.
- No speaker ID: a speaker may have read several sentences, so the recordings are not fully independent.
- Gender is FLEURS's label, in two values only. Use it only to compare groups, never to guess a person's gender from their voice.
- The sentences come from FLoRes (Wikipedia sentences translated; FLoRes is CC BY-SA 4.0). FLEURS is released under CC BY 4.0; we download the text from FLEURS itself and keep the attribution.
- The speakers are real volunteers. Do not try to identify them, and do not use their voices to train a voice clone.
