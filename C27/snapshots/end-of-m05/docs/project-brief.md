# Project brief: the document assistant

Sam's brief for the worked capstone, written with Grace (Larkfield's support lead) and Ines (the owner of Bramble Books).

## User and decision

- Who uses the product: the help-desk staff of two small shops, Larkfield (home and garden) and Bramble Books (an independent bookshop).
- The decision it helps with: answer a customer's policy question correctly, from the shop's own documents, while the customer waits.
- How they do it today, and what goes wrong: staff search a shared folder and read several documents. Last month a Larkfield agent quoted the old 30-day return window to a customer whose delivery fell under the new 45-day policy, and a Bramble Books volunteer quoted the FAQ's "5 business days" for a special order that took 9.

## Documents

- Which documents the product reads: each shop's own policies, staff procedures, help articles and supplier notes. Larkfield: 36 documents (Markdown, HTML and PDF). Bramble Books: 15 documents.
- Who owns them, and why we may use them: every document is synthetic, written for this course; no real company wrote them. Licence CC0.

## What success looks like

- A member of a shop asks a question in plain words and gets, in a few seconds, a short answer with a citation for every claim, or a clear "the documents do not answer this".
- A shop never sees the other shop's documents, passages or answers.

## Non-goals

- No answers sent to customers directly: staff read the answer and decide.
- No chat history and no follow-up questions: one question, one answer.
- No agent that takes actions (refunds, emails). Tomás asked for one; it is a possible extension after the core works.
- No other languages than the documents' (English, and French for Larkfield's two Quebec documents).
- No cloud deployment in the core: a reproducible local demonstration.

## Track

- [x] Standard track: the supplied two-shop data pack
- [ ] Own-idea track

## Milestones

| Milestone | Done when | Week |
|---|---|---|
| Design pack | the architecture and the threat and cost review are written and reviewed by Kwame | 1 |
| One journey | Grace uploads a document, sees it indexed, asks a question and gets a cited answer | 2 |
| Safe and reliable | the wrong-shop, missing-source, invalid-file and provider-timeout cases pass | 3 |
| Evaluated | the held-out report is written and Priya reviewed it | 4 |
| Shipped | a clean computer runs the demo from the README; Omar has seen the demo | 5 |
