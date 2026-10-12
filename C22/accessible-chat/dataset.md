# Dataset card: recorded answers of Larkfield's policy assistant

Used by: the case study *Make an AI chat interface accessible* of *Frontend Architecture and Performance for AI Apps* (Nextia Learning), the project `policy-chat` (`mock/data/replies.json`).

| Field | Value |
|---|---|
| Source | Nextia Learning's RAG course: Grace's 67 questions ([labs `C09/questions/`](https://github.com/usmanahmed99/nextia-learning-labs/tree/main/C09/questions)) and the recorded answers of the course's policy assistant (retrieval with reranking, model `chat-small`) |
| Publisher / creator | Nextia Learning. The questions and the policy documents are made up for the courses; the answers are the real output of a hosted language model, recorded once. |
| Licence | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (public domain) |
| Attribution text | None needed. "Recorded policy-assistant answers, Nextia Learning" is welcome. |
| Version or access date | 1.0. Made by a script from the committed recordings; the same input always gives the same bytes. |
| File used | `mock/data/replies.json`, kept in the project: yes |
| SHA-256 | `dbffdaddb228f510e8c51415e518b3dc374fb106ace4474f4257dcb6de62b701` (`mock/data/SHA256SUMS`; check with `shasum -a 256 -c SHA256SUMS` in `mock/data/`, or `sha256sum -c SHA256SUMS` on Linux) |
| Size | 67 replies × 10 fields, 34,467 bytes |

## What one row means

One question that a help-desk agent asked about Larkfield's policies, and the assistant's answer: the text
(one to three sentences), its sources (document and section), whether the documents answer the question
(`answerable`), the language (`en` or `fr`), and the timing of the recorded call: `recorded_ms` (the whole call),
`first_piece_ms` and `piece_gap_ms` (how the mock streams it). There is no target: the replies are what the chat
shows and what a screen reader must hear.

## Why this dataset

The chat needs real answers with real waiting times, in more than one language, under a clear licence. The two
public alternatives compared were OpenAssistant oasst1 (Apache-2.0: human-written conversations in 35 languages,
no timing, about 105 MB) and databricks-dolly-15k (CC BY-SA 3.0: ShareAlike is outside the licences that the
course uses). These recorded answers are small, real model output, timed, and 9 of them are in French, which
makes "the language of each reply" a real problem.

## Changes we made

Only one of the four recorded runs is kept (retrieval with reranking, `chat-small`). The answers' claims and
passages are dropped; each source keeps its document name and section. The streaming time is simulated from the
recorded time, as in the course's mock API: the first piece after most of the call's time, then a piece every
few milliseconds. A piece is a word or a punctuation mark, not one of the model's tokens.

## Limitations and cautions

- The policies and Larkfield are made up. The answers are a model's output: some are incomplete or wrong, as in
  the RAG course's evaluation. The chat must show them as answers to check.
- 13 of the 67 answers say that the documents do not answer the question.
- The mock chooses the recorded answer whose question shares the most words with yours. It does not understand
  questions; a question that matches none gets a fixed "no recorded answer" reply.
- 67 short answers: enough to test an interface, not to judge the assistant.
