# Dataset card: MASSIVE 1.1 (English and French, 4 scenarios)

Used by: the case study *Sort requests with few labels* of the course *Text Classification and Routing* (`sort-requests-with-few-labels.ipynb`, `sort-requests-with-few-labels-solution.ipynb`)

| Field | Value |
|---|---|
| Source | https://github.com/alexa/massive (the README links the archive https://amazon-massive-nlu-dataset.s3.amazonaws.com/amazon-massive-dataset-1.1.tar.gz). A loader is on Hugging Face as `AmazonScience/massive`. |
| Publisher / creator | Amazon (Alexa AI): Jack FitzGerald, Christopher Hench, Charith Peris and others. MASSIVE translates and localises the English text of SLURP (Emanuele Bastianelli, Andrea Vanzo, Pawel Swietojanski and Verena Rieser). |
| Licence | CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ (the archive's `LICENSE` file; SLURP's text is also CC BY 4.0, see the archive's `NOTICE.md`) |
| Attribution text | "MASSIVE 1.1" by FitzGerald et al. (Amazon), https://github.com/alexa/massive, CC BY 4.0, built from SLURP by Bastianelli et al., CC BY 4.0. Papers: "MASSIVE: A 1M-Example Multilingual Natural Language Understanding Dataset with 51 Typologically-Diverse Languages", 2022, https://arxiv.org/abs/2204.08582; "SLURP: A Spoken Language Understanding Resource Package", EMNLP 2020, https://aclanthology.org/2020.emnlp-main.588/. |
| Version or access date | MASSIVE 1.1 (the archive's `CHANGELOG.md`: 1.1 adds Catalan to 1.0). |
| File used | `1.1/data/en-US.jsonl` and `1.1/data/fr-FR.jsonl` from the archive. Not kept in this folder: the notebook downloads the archive, checks its SHA-256, keeps the two files and deletes the archive. |
| SHA-256 | archive `4cba5faa11c71437928e17cb1b9b3d8b8e727e7ea363a3a9a8045e19c0491577` (40,251,390 bytes); `en-US.jsonl` `c70f75c6a543a26e249ec383df67733ad9b1066f6c0406c2e04a3f03356e407e`; `fr-FR.jsonl` `f9bf3db170ad415b389e4c9594dd0f8f80c38188143e05cc4459a6fa7df7cf49` |
| Size | each file 16,521 rows (one JSON object per line), 3.9 MB (English) and 12.2 MB (French, with the translators' quality notes). The case study keeps 5,094 rows per language. |

## What one row means

One row is one short request that a person could say or type to a digital assistant, such as "wake me up at nine am on friday", with its **intent**: what the person wants done, here `alarm_set`. The French row with the same `id` is a translation of the English one ("réveille-moi à neuf heures du matin le vendredi") and has the same intent. The task is to predict the intent.

## Why this dataset

It has the same requests in English and in French, with intent labels, under a licence that allows reuse with credit. So the case study can draw the "how many labels do you need" curve in both languages on the same requests, and ask whether English labels are enough for French. We keep the requests of a calendar, email and list assistant (13 intents), which have close neighbours (set, ask and delete for the same object). We compared it with HWU64 and SLURP (CC BY 4.0, English only), a re-packaged copy on Hugging Face whose stated licence does not match the original, and Bitext's customer-support set (CDLA-Sharing-1.0, a licence that the course does not use).

## Changes we made

- We keep 4 of the 18 scenarios: `alarm`, `calendar`, `email` and `lists` (13 intents), and the columns `id`, `partition`, `scenario`, `intent` and `utt`.
- We renamed `utt` to `text` and the partition `dev` to `validation`, and added `language` (`en`, `fr`) and `message_id` (`MA-en-1`, `MA-fr-1`, …).
- We use MASSIVE's own split: train 3,570, validation 613 and test 911 requests per language.
- The other files in this folder are ours, released with the course under CC BY 4.0: `data/intents.csv` (a short description of each intent, the words that the zero-shot models and the LLM read, and which intents we treat as costly to miss) and `recordings/llm-*.jsonl` (answers of a hosted LLM, recorded once for every validation and test request, so that you need no key).

## Limitations and cautions

- The requests were written by crowd workers for a voice assistant. They are not messages typed by real customers of a product. The English text is lower-case, without punctuation, and numbers are written as words ("nine am").
- The French is a translation of the English. It follows the English closely, so French results here are an optimistic guide for French that people write themselves. Some translations are wrong: "through outlook" became "à travers les perspectives" (the name of the program was translated), and at least one French row says the opposite of its label.
- Some labels are borderline or wrong, as in SLURP: "remind me …" is `calendar_set`, never `alarm_set`; very short rows such as "nice" (labelled `calendar_set`) carry no intent at all.
- A few texts repeat: 11 in the English training part and 51 in the French one; 7 English and 29 French test texts also appear in training.
- Each request has exactly one intent. Real messages often ask for two things.
- Scores on this set do not tell you how a method works on your own users' requests. Test on your own data.
