# Dataset card: AMI Meeting Corpus (four scenario meetings, with recorded outputs)

Used by: the case study *Meeting transcripts with speakers* of the Speech AI course, `meeting-transcripts-with-speakers.ipynb`

| Field | Value |
|---|---|
| Source | AMI Meeting Corpus, https://groups.inf.ed.ac.uk/ami/corpus/ (audio: `AMICorpusMirror/amicorpus/<meeting>/audio/`; annotations: `ami_public_manual_1.6.2.zip`) |
| Publisher / creator | The AMI Consortium; hosted by the University of Edinburgh (Centre for Speech Technology Research) |
| Licence | CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ (corpus licence page: https://groups.inf.ed.ac.uk/ami/corpus/license.shtml; `LICENCE.txt` in the annotations zip) |
| Attribution text | "AMI Meeting Corpus, University of Edinburgh and the AMI Consortium, CC BY 4.0 (groups.inf.ed.ac.uk/ami/corpus). Excerpt cut and converted to FLAC by Nextia Learning; word reference extracted from the AMI manual annotations 1.6.2." |
| Version or access date | Manual annotations 1.6.2; audio from the Edinburgh mirror, downloaded 2026-11-08 |
| File used | `data/` in this folder: kept (the licence allows redistribution with attribution) |
| SHA-256 | every file in `data/SHA256SUMS`; annotations zip `b56e5babb2496b8795deeeda7e71178d7fbc9963f94276cf2a3f4b56ebbc9f9d` |
| Size | 27 MB: 5 FLAC files (5 minutes each), 1 reference JSON, 4 Whisper JSONL (tiny, base, small, small with its VAD), 1 diarization JSON, 1 action-items JSONL |

## What one row means

- `data/audio/IS1008a-excerpt.<stream>.flac`: 5 minutes (10:40 to 15:40) of meeting IS1008a, from one of the four headsets (`Headset-0` to `Headset-3`, one per person) or the far microphone on the table (`Array1-01`), 16 kHz, 16-bit.
- `data/reference.json`: for each of four meetings (ES2004a, IS1009a, IS1001a for the comparison; IS1008a as new input): its length, the four speakers (letter A–D, headset channel, role, sex, native language as given in the AMI participants file), every word with its start and end time and speaker, the true turns (one speaker's words joined while the gap is under 0.5 s), and the "actions" sentences of the AMI abstractive summary.
- `data/recorded/whisper-{tiny,base,small,small-vad}.jsonl`: one row per meeting and stream: the words Whisper wrote with their times, and the compute seconds (faster-whisper 1.2.1, int8, 4 CPU threads, beam 1, Apple M4).
- `data/recorded/diarization.json`: the turns (start, end, speaker) of every diarization method of the case study, per meeting.
- `data/recorded/action-items.jsonl`: the action items that Azure chat-small wrote from three kinds of transcript per meeting (text only; no audio was sent), with the prompt, the transcript text, tokens and cost.

## Why this dataset

AMI is one of the few open meeting corpora that has, for the same meeting, one headset per person and a far microphone, word-level times per speaker, and a human summary with action items, under CC BY 4.0. The Hugging Face copy (`edinburghcstr/ami`) is cut into utterances and has no word times or summaries; ICSI (also CC BY 4.0) has longer meetings with more channels; VoxConverse's audio comes from YouTube with unclear terms. See the course's research notes for the comparison.

## Changes we made

The excerpt is cut from the original WAV files and stored as lossless FLAC; nothing else changed in the audio. The reference keeps AMI's words without punctuation tokens and vocal sounds, with the HTML entity `&#39;` turned back into an apostrophe. The recorded outputs are ours.

## Limitations and cautions

- Real people, recorded with their consent for research use. Do not try to find out who they are; the course uses only AMI's letters and roles.
- Role-play meetings about designing a remote control, recorded in 2005 in three instrumented rooms: spontaneous speech, but a fixed topic and good microphones.
- Twelve speakers in the three comparison meetings are too few for conclusions about groups (sex, first language).
- Word-based true turns count short pauses inside a turn as speech, which raises the missed part of the DER for every method.
