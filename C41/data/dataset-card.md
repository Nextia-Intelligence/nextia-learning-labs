# Dataset card: the Larkfield calls (synthetic)

**Every call in this folder is synthetic.** Larkfield is an invented online shop. The scripts were written by our
code (with fixed random seeds) and, for the callers' own sentences, by a language model; open text-to-speech voices
then read them. No real customer, no real call and no real person's voice is in this data. Never use real customer
calls for practice: they hold voices, names and sometimes card numbers, and the people did not agree to it.

## What is here

| Folder or file | What |
|---|---|
| `calls/calls.jsonl` | One line per call: `call_id`, `split` (train, validation, test), `language` (en, fr), `reason`, `promise`, `next_step`, `notice` (exact, variant, missing), `line`, `noise`, `channels`, `accent`, `duration`, `planted`, `important` (order numbers, products, dates, negations, card numbers), `voices`, and `turns` (speaker, start, end, `text` = the reference transcript, `spoken` = what the voice read, `words` with times). |
| `calls/phone/<id>.wav` | The phone recording: 8 kHz, G.711 mu-law (what a phone system stores). Stereo (channel 1 the agent, channel 2 the caller) or mono. |
| `calls/wideband/<id>.flac` | The same call at 16 kHz, mono, after a G.722 (HD voice) codec. |
| `ivr/calls.jsonl`, `ivr/<id>/NN.wav` | The IVR test calls: the caller's side only, one file per caller turn (speech, keypad tones or silence), with the expected path and outcome. |
| `noise/` | Music on hold, background talk, street noise and line noise (20 s each, 16 kHz). |
| `tts/` | The IVR prompts read by Piper and Kokoro, on a phone line (8 kHz). |
| `recordings/` | Recorded outputs: `asr/<method>.jsonl` (transcripts of each recogniser), `llm/` (call records written by a hosted language model), `agent/` (the voice agent's turns). Replayed by the course project: you need no key. |
| `orders.json` | The fake order system: 160 orders (6-digit numbers with a check digit). |
| `normalisation-guide.md`, `vocabulary.json` | The written normalisation guide and Larkfield's words. |
| `costs.json`, `prices.json` | Cost assumptions, and hosted prices to check before you quote them. |
| `voices.json` | Every voice used, with the licence of its model and its training data. |
| `comparison_table.json` | The measured comparison table. |
| `SHA256SUMS` | A checksum of every file (`speech reset` checks them). |

Only the validation and test calls have audio; the train calls have their transcripts and labels (enough to train a
text classifier). A hidden test set and the final assignment's calls are kept by the course team.

## How the calls were made

- **Scripts:** templates for the agent and for the order numbers, dates and promises; the callers' own sentences
  (why they call) were written by a hosted language model from a list of reasons, products and moods, then checked
  by code (no digits, no names). Reference transcripts come from the scripts, so they are exact.
- **Voices** (`voices.json`): Piper voices trained on LibriTTS-R (CC BY 4.0), the CSTR VCTK corpus (CC BY 4.0),
  LJ Speech (public domain), SIWIS (CC BY 4.0) and a CC0 French single-speaker set; and Kokoro-82M (Apache-2.0).
  Each multi-speaker voice was screened: a speaker is used only if a recogniser writes back two test sentences
  almost exactly. French has only three voices (two learned from the same speaker), so French speaker variety is low.
- **The line:** each side of the call is band-limited to 300-3,400 Hz, coded (G.711, a mobile Opus line at 8 kbit/s,
  or G.726 at 16 kbit/s), and stored as 8 kHz mu-law. Background talk is other synthetic voices; street noise and
  music on hold (a public-domain melody) are made by code.
- **Practice problems we made on purpose** (`planted`): long silences while a caller looks for a number or is on
  hold with music; order numbers said in pairs or with a pause; French callers who switch to English; calls without
  the recording notice; a card number said aloud; an agent and a caller with almost the same voice.

## Limits (read before you trust a number)

- Synthetic voices are cleaner and more regular than people: no real hesitations, no talking over each other, no
  real accents beyond what each voice learned. Errors on real calls are higher. Use the case studies for real speech.
- Part of the French error rate comes from the voices themselves, not from the recognisers.
- The calls are short (about 30 to 60 seconds) and follow a few patterns.

## Licence

The calls, labels and recordings in this folder: CC BY 4.0, with the attribution of the voices' training data in
`voices.json` (LibriTTS-R, VCTK and SIWIS are CC BY 4.0). Music on hold and noise: made by our code (CC0).
