# Dataset card: the Harbourton practice pilot, and the public MyCity chatbot case

Used by: the case study *Could the records have answered?* of the course *Observability for AI Agents*,
`starter.zip` and `finished.zip` (project folder `could-the-records-answer`)

| Field | Value |
|---|---|
| Source | Made for this case study by Nextia Learning: `data/pages/`, `data/questions.json`, `data/releases.json`, `data/labels.json`, `recordings/chat-small.jsonl`; the pilot's records are made on your computer by `python pilot.py`. The public case it is modelled on is linked in `CASE.md`. |
| Publisher / creator | Nextia Learning |
| Licence | MIT (the project's `LICENSE`), code and data. The public sources are not part of the data: they are linked, never copied. |
| Attribution text | "Harbourton practice pilot, Nextia Learning (MIT)." |
| Version or access date | Version 1 of the case study. The public sources were read for it and are linked in `CASE.md`. |
| File used | All files are in the project folder: yes. Nothing is downloaded. |
| SHA-256 | `recordings/chat-small.jsonl`: `f27194f8c944f3a2b0d0b96c9ed53095ebe9742ac5bbecd125b2f2a06cacec61` (297,636 bytes). The pilot is seeded: `python pilot.py` writes the same records every time (the tests check the counts). |
| Size | 11 practice rule pages; 8 questions; 4 release lines; 170 recorded model answers (17 requests × 10 samples); the pilot: 2,783 conversations, 3,359 answers over 190 practice days, about 10 MB of records in four designs. |

## What one row means

One recorded answer is one real reply of the course's `chat-small` model deployment to one exact request: the
system prompt of a release, the two pages that the search found, and one of the eight questions. One pilot
conversation is a constructed visit to the practice helper: a day, a person (an account or an anonymous
session), one or two questions, and the replayed answers. The label of an answer (`data/labels.json`) says
whether it agrees with the practice page of its question: right, wrong, incomplete or referred.

## Why this dataset

The case study needs the records of an AI assistant whose answers a public body had to defend. No such records
are public: the real city's chat data is not published, and its page said that it deleted data within 30
days. So we build a small assistant with the same parts (a search over rule pages, a model, a warning, a
feedback form), record real model answers to its requests, and replay them in constructed traffic. Then the
records of every design can be compared on the same events. We chose the MyCity case over four others (an AI
support agent that invented a policy, a parcel chatbot that swore, a court case about invented citations and a
car dealer's chatbot): it has official sources, a public defence, a stated retention period, a changed warning
and a feedback form, and each of them is a question to a system's records.

## Changes we made

None to any public source: we copy none. The practice pages are short rules that we wrote for a made-up city.
Two of them are out of date on purpose: the index of release 1.0 holds an old copy of the cash page, and the
minimum-wage page changes on day 171 while the index keeps the old version until day 185.

## Limitations and cautions

- **Harbourton is not New York City.** Its rules are made up and are not legal advice. Nothing here says what
  the real chatbot said, recorded or kept, or why its answers were wrong.
- **The traffic is constructed:** fixed question texts, no other languages, made-up rates of sign-in (25%)
  and of feedback. Real people ask in their own words, so a real topic code makes more mistakes.
- **The model's answers are real but few:** 10 samples of 17 requests, from one deployment, at one time.
  In this setup the model followed its pages: every wrong answer came from an out-of-date page. A real
  assistant with 2,000 pages and free questions also makes model errors.
- **The labels are ours:** a person checked each distinct answer against the practice page, once.
