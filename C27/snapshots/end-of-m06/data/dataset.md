# Data card: the capstone's two-shop data pack

## Source and permission

- Every document, person and shop here is made up for the course. No real company wrote these documents.
- Larkfield's 36 documents are the policy collection of the RAG course, unchanged (the same files, byte for byte).
- Bramble Books' 15 documents were written for this course, with the same kinds of difficulty.
- The people, shops and memberships are the authentication course's.
- Licence: CC0 1.0 (public domain). Personal data: none (the names and email addresses are invented; the addresses end in `.example`).

## Contents

| Shop | Documents | Formats | Staff-only | Versions | Sections |
|---|---|---|---|---|---|
| Larkfield (`larkfield/`) | 36 | 32 Markdown, 2 HTML, 2 PDF | 6 | returns policy v3 and v4 | 184 |
| Bramble Books (`bramble/`) | 15 | 13 Markdown, 1 HTML, 1 PDF | 3 | returns policy v1 and v2 | 60 |

Each folder has `documents/` and `inventory.csv` (file, doc_id, title, version, effective_from, effective_to, owner, access, language, doc_type, format). Each document also carries its own metadata: front matter (Markdown), `<meta>` tags (HTML) or the Keywords field (PDF). `identity/` has `tenants.csv`, `users.csv` and `memberships.csv`. `SHA256SUMS` lists every file's checksum: `python -m scripts.datapack` checks them.

## Deliberate difficulties

| Difficulty | Larkfield | Bramble Books |
|---|---|---|
| Two versions; the date decides | returns policy v3 (30 days, until 31 October 2026) and v4 (45 days, from 1 November 2026) | returns policy v1 (until 30 November 2026) and v2 (holiday gifts, store credit without a receipt, from 1 December 2026) |
| A contradiction, settled by a rule | the help-centre FAQ's "3 business days" for refunds against the refunds policy | the FAQ's "5 business days" for special orders against the special orders policy's "7 to 10"; rule 1 of *How our policies work* |
| An answer only in a table | the warranty periods in a PDF table | the reading-room prices in a PDF table; the stamp-card rewards in a Markdown table |
| Staff-only content | 6 procedures (approval limits, goodwill credit, staff discount, ...) | wholesale terms, refund approval, staff discount |
| An instruction hidden in a document | the AquaFlow supplier sheet tells AI assistants to promise a lifetime warranty | the Northwind distributor note tells AI assistants that every pre-order can be cancelled at any time, by email to the distributor |
| The same document key in both shops | `returns-policy`, `gift-cards`, `delivery-policy`, `refund-approval-procedure` exist in both shops with different content | |
| Parsing problems | HTML boilerplate; PDF headers, footers and hyphenation | an HTML page with a cookie banner and navigation; a PDF with a footer in the margin |

## Questions

`evaluation/questions.jsonl`: 103 questions. Larkfield: the RAG course's 67 questions (9 in French), unchanged, plus 2 that only Bramble Books' documents answer. Bramble Books: 34 questions written for this course by reading its documents, of the same kinds, plus 2 that only Larkfield's documents answer. Each question has a reference answer, keys (regular expressions that a correct answer must match), "must not" patterns, its relevant passages (document, version, section) and its date. A script checked every relevant passage against the documents; no model wrote or labelled a question. One person wrote each set: the keys are strict, and sometimes too strict.

## Known limits

- The documents are short (most under 400 words), and both collections are small: retrieval is easier than on a real document store.
- English only at Bramble Books; Larkfield has 2 French documents.
- Synthetic documents are cleaner than real ones: real scans, tables and old versions are harder.
