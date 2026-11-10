# Dataset card: Speech Commands v0.02 (a fixed sample)

Used by: the case study *Spot commands on a small device* (Speech AI course), `spot-commands-on-a-small-device.ipynb`

| Field | Value |
|---|---|
| Source | https://arxiv.org/abs/1804.03209 (paper); archive http://download.tensorflow.org/data/speech_commands_v0.02.tar.gz; Hugging Face card https://huggingface.co/datasets/google/speech_commands |
| Publisher / creator | Pete Warden, Google (TensorFlow and AIY teams); recordings by volunteers |
| Licence | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (the `LICENSE` file in the archive, copied here as `data/LICENSE-speech-commands.txt`) |
| Attribution text | "Speech Commands v0.02" by Pete Warden (Google), https://arxiv.org/abs/1804.03209, licensed under CC BY 4.0. Sample, log-mel pictures and kitchen recording made by Nextia Learning. |
| Version or access date | Version 0.02 (released 11 April 2018); the archive downloaded on 8 November 2026 |
| File used | A fixed sample, kept in `data/`: yes (CC BY 4.0 allows sharing with credit; the original is 2.4 GB) |
| SHA-256 | Every file in `data/SHA256SUMS`; the notebook checks each one |
| Size | 10,905 items (9,185 one-second clips and 1,720 noise windows) as log-mel pictures, 40 × 98 values each; 24 test clips and one 19-second recording as WAV; about 36 MB |

## What one row means

One row of `clips.csv` is one second of audio: a person saying one word (`class` is the command, or `other` for a word that is not a command), or a one-second window of background noise (`noise`). `speaker` is the dataset's random speaker ID; `split` is train, valid or test. The matching picture in `speech-commands-sample.npz` is its log-mel spectrogram: 40 mel bands (20–7,600 Hz) by 98 frames of 10 ms, in dB, stored as one byte per value (−100 dB to +27.5 dB in steps of 0.5 dB).

## Why this dataset

It was made for this task: one-second clips of 35 words from 2,618 volunteers, with ten standard commands, other words for false alarms, background-noise recordings, and an official speaker-disjoint split. The alternatives compared: the Multilingual Spoken Words Corpus (CC BY 4.0, but cut automatically from sentences, and many GB); Fluent Speech Commands and the Snips wake-word data (research-only terms); Common Voice single words (CC0, but the download needs an account).

## Changes we made

- **Sample** (chosen by a hash of each file path, the same on every run): train 300 clips of each command (on 293, off 292: all the subset had) + 1,600 clips of other words (official training files); validation 60 of each command + 1,200 other words (official validation list); test 100 of each command (from the official test-set archive) + 1,800 other words (official testing list). Splits follow the dataset's own rule (a hash of the speaker ID), so no speaker is in two splits.
- **Background noise:** each of the six files is cut in time: the first 60% for training (one-second windows every 0.5 s, at three volumes: as recorded, 0.3 and 0.05 times), the next 20% for validation and the last 20% for testing (as recorded).
- **Pictures, not audio:** each clip is stored as its log-mel picture (the notebook's own `log_mel` code). 24 test clips are also kept as 16-bit WAV.
- **The kitchen recording** (`audio/kitchen-stream.wav`): the test part of `doing_the_dishes.wav` at half volume, with six test clips (yes, bed, stop, go, seven, off) added at the times in `stream.json`. It is a constructed example, not a real recording of a kitchen.
- **Recorded outputs:** Whisper tiny (faster-whisper, int8, with the ten words as a prompt) and Vosk small (with a grammar of the ten words) were run once on every validation and test item; `recordings/latency.json` has their speed on one CPU thread.

## Limitations and cautions

- **No groups.** The dataset kept no age, gender, accent or location of the speakers. Results can be split by speaker and by word only.
- **Isolated words.** Every clip is one word, cut to its loudest second. Real speech near a device is sentences, music and television; the false alarms here are on isolated words and six noise recordings only.
- **Few hours of negatives.** The test has 30 minutes of other words and 76 seconds of new noise. That cannot show a rate like "one false alarm a day".
- **Recording quality varies** (phones and laptops in people's rooms); some clips are quiet, cut short or hard to understand. The dataset's own screening removed many but not all.
- **English only**, and the speakers are volunteers who chose to take part, not a sample of any population.
