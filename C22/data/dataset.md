# Dataset card: Larkfield help-desk data for the ticket desk

Used by: every lesson of [Frontend Architecture and Performance for AI Apps](https://learning.nextia-ai.com/courses/frontend/), through the project's mock API (`mock-api/data/` in every snapshot).

| Field | Value |
|---|---|
| Source | Made up for Nextia Learning's courses, and recorded answers of real AI models from earlier courses (see below). |
| Publisher / creator | Nextia Learning |
| Licence | CC0 1.0 (public domain) |
| Attribution text | None needed. |
| Version | 1.0. A script makes the files from the earlier courses' files; the same input always gives the same bytes. |
| Files | `tickets.json` (270 tickets), `drafts.json` (70 AI drafts), `timing.json` (recorded times). The same files are in `mock-api/data/` of every snapshot. |
| SHA-256 | `SHA256SUMS` (check with `shasum -a 256 -c SHA256SUMS`, or `sha256sum -c SHA256SUMS` on Linux) |
| Size | 0.24 MB in all |

## What one row means

- **`tickets.json`:** one support request to Larkfield, a made-up online home-and-garden shop: the ticket ID, the customer (ID and name), the subject, the customer's message, the channel, the team (`billing`, `login`, `shipping`, `account`, `other`), the priority (1 is the most urgent), the status, the time, and the later messages.
- **`drafts.json`:** one AI draft of a reply to one ticket: the reply text, `needs_human` (true when a person must handle the ticket), the reason, the model's confidence (`high`, `medium`, `low`), and for some drafts the sources: claims with the passage of a policy document that supports each one.
- **`timing.json`:** the recorded times of earlier model calls: three streamed answers (when each piece of text arrived) and 100 calls of each background task (classify, draft a reply, embed).

## Where it comes from

- **200 tickets** (`T-30001` to `T-30200`) are the small practice data of the databases course: made up by a script.
- **69 tickets** (`T-64701` … `T-80009`) are the evaluation tickets of the LLM applications course: made up by the course team. Their subject is the first words of the message (those tickets had no subject), and their customers' names are made up here.
- **The 69 drafts** are the real answers of a hosted language model (`chat-small`) to those 69 tickets, recorded in the LLM applications course. They are replayed, not made again.
- **The sources** of 9 drafts are the real recorded answers of the RAG course's policy assistant to the policy question that the ticket raises (for example "How long does a refund take to reach the customer's card?"). The course team chose which question goes with which ticket. For one of them, the assistant answered that the documents do not say.
- **1 ticket and its draft are constructed** (`T-80010`, model `constructed-example`): a draft in Markdown that also holds an HTML tag with code in it, for the security lesson. No model wrote it.
- **The large size** (10,000 tickets) adds made-up tickets `T-100001` and up, made by the mock API from the same texts with a fixed seed. They are not in these files.

## Why this data

It is the same shop, the same customers and the same kind of tickets as in the earlier courses, so the interface shows data that learners know. The drafts and their times are real model output, so the interface handles real text and real waiting times, without a model, an account or money.

## Changes we made

The teams of the LLM applications course (delivery, returns, payment, warranty, account) became the ticket API's teams (shipping, other, billing, other, account). The priority of those 69 tickets is constructed: 1 when a person must handle the ticket, else 2.

## Limitations and cautions

- Everything is made up, except the model answers, which are a model's output for made-up tickets. No real person's data is in it.
- The tickets come from a few dozen templates: many are very similar.
- The drafts were checked by the course team only in the earlier courses' evaluations; some are wrong or incomplete, as model output can be. The interface must show them as drafts that a person checks.
- The times of the mock API's answers are simulated (a list answer: 60 ms plus 0.1 ms per matching ticket). The times of drafts and background jobs come from the recordings; slow, failing and interrupted modes are constructed.
