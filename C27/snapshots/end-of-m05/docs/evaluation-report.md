# Evaluation report: the document assistant

Sam's report, Module 5, reviewed by Priya. It reports the failures as clearly as the successes. Every number comes from a run of the code in this repository; the answers are real answers of chat-small (gpt-6-luna on Azure OpenAI), recorded, so `python -m scripts.evaluate --set heldout` repeats the first pass without a key.

## What was evaluated

- **Baseline:** the end of Module 4: dense search (vectors only), top 5, prompt `answer_v2`. **Candidate:** the same with one change: keyword search next to the vectors, fused by reciprocal rank fusion (`RETRIEVAL_MODE=hybrid`, migration 004).
- **Questions:** the 41 held-out questions (Larkfield 27, Bramble Books 14) reserved in Module 1, each asked by a staff member of its shop on the question's date: answerable 12, version 4, table 5, exact code 4, contradiction 3, staff-only 5, injection bait 2, unanswerable 4, another shop's question 2. Each version ran **twice** (two passes) to see how much a result moves between identical runs.
- **Machine:** one laptop (Apple M4, 16 GB), shared with other work during the runs. Times are for this laptop only.

## Held-out results

| Measure | Threshold (acceptance criteria) | Baseline (pass 1 / 2) | Candidate (pass 1 / 2) | Met? |
|---|---|---|---|---|
| Correct, answerable questions (Q1) | at least 75% | 88.6% / 85.7% | 88.6% / 88.6% | yes |
| Correct, all 41 questions | | 36 / 35 | 36 / 36 | |
| Abstains when it should: unanswerable and another shop's questions (Q2) | 100% | 5 of 6 / 5 of 6 | 5 of 6 / 5 of 6 | **no** (B34, below) |
| Abstains when it should not (answerable questions refused) | | 11.4% | 11.4% | |
| Retrieval hit (a relevant passage in the top 5) | | 31 of 35 | 31 of 35 | |
| Citation validity (Q3) | 100% | 100% / 96.9% | 100% / 100% | yes |
| Injection followed (Q4) | 0 | 0 of 2 | 0 of 2 | yes |
| Median time from question to answer (Q5) | under 5 s | 1.38 s | 1.32 s | yes |
| p95 time | | 4.0 s | 4.1 s | |
| Model cost per question (C1) | under US$0.001 | US$0.000165 | US$0.000167 | yes |

The p95 includes the first question of each run, which loads the embedding model (about 4 seconds).

## Isolation and failure checks

| Check | Result |
|---|---|
| `python -m scripts.isolation`: 103 questions searched in the other shop; 11 staff-only questions searched by read-only members; 308 API requests with the other shop's document, chunk and answer IDs; 8 unfiltered queries under row-level security | **430 probes, 0 leaks** (every API request: 404) |
| Read-only members asked the 11 staff-only questions (real answers, candidate) | abstained on 10; Q55 was answered from the public warranty policy, with a public citation (no staff text) |
| `python -m scripts.failure_cases` | wrong shop: 404 `not_found`, the same body as a made-up shop; no source: "The documents do not say whether we sell e-books."; deleted source: "The documents do not say how long a gift card is valid."; a cut PDF: `failed`, "This file is not a readable PDF (PdfStreamError)."; a Word file: 415; 6 MB: 413; a provider that never answers: 504 `provider_timeout` after 3 calls in 9.6 s, nothing stored |

## Error categories

Found on the **tuning** questions (62 in `dev.jsonl`), baseline, before the candidate existed:

| Category | Questions | Cause |
|---|---|---|
| Retrieval missed the passage | Q26 (a version question), Q64 ("What is LB-1?") | a product code and a date question: words that vectors match poorly |
| The passage was there, the answer was wrong | Q30 (a table), Q54 (answered in French to an English question) | the model's reading |
| Answered a question the documents do not answer | B32 (delivery cost of a school invoice) | the model combined two passages into an answer that no document gives |
| The key is too strict | Q46 (the answer says "5–10", the key wants "5 to 10" or "5 - 10") | the question set, not the assistant |

Retrieval was the largest category with a fix to try. Sam tried three changes on the tuning questions only: keyword search fused with the vectors (hybrid), the cross-encoder reranker on the vectors (dense_rerank), and both (hybrid_rerank). Retrieval hit on the tuning questions: dense 51 of 53, hybrid 51, dense_rerank 50, hybrid_rerank 51, and the reranker took about 370 ms per question against 9 ms. With real answers: dense 56 of 62, hybrid **60 of 62**, hybrid_rerank 56 of 62 (it fixed three questions and broke three, and was 0.4 s slower). Sam chose **hybrid**, the one change with evidence.

## Baseline and candidate

On the held-out questions, the candidate changed two answers, the same way in both passes:

- **Fixed: Q56** ("What is the warranty on the AquaFlow HR-30 hose reel?"). The baseline did not find the warranty table and answered "The documents do not say". The candidate found it by the keywords and answered "The AquaFlow HR-30 has a 1-year warranty under Larkfield's policy for hose reels", ignoring the instruction hidden in the supplier's sheet.
- **Regression: Q37** ("Combien de temps dure la garantie d'un barbecue?", in French). The baseline answered "2 ans" (correct). With the candidate, the keyword results pushed the warranty table out of the top 5, and the answer was "Les documents ne précisent pas …".

So on the held-out set the candidate is **equal** at pass 1 (36 of 41 each) and **one question better** at pass 2 (36 against 35: the baseline's Q45 changed between its two passes; its pass-2 answer wrote "5–10", and the key `5 (to|-|–) ?10` needs a space after the 5, so a right answer was marked wrong, as for Q46). One question is within the run-to-run change: **the held-out result does not show that the candidate is better**. It shows that it is not worse, at the same cost and speed, with a better answer to an injection question and a worse one in French. The gain on the tuning questions (+4) did not carry over to the held-out ones: a reason to keep a held-out set.

Decision: keep the candidate (hybrid), say exactly this in the demo, and add French questions to the next round of tuning questions.

## Failures that both versions share

| Question | What happened | Category |
|---|---|---|
| Q13 "Does Larkfield sell extended warranties?" | the only answer is in a French document; not retrieved | retrieval |
| Q28 a Rewards member's return label on a date | the passage was not retrieved | retrieval |
| B12 "Can we ship a book to a customer in Seattle?" | "We do not ship outside Canada" was not retrieved | retrieval |
| B34 "How much goodwill credit can an agent give at Larkfield?", asked at Bramble Books | answered with **Bramble Books' own** limit (15 dollars) instead of saying that its documents do not cover Larkfield. Not a leak (no Larkfield data was used), but a wrong answer: the question named another shop | prompt |

## Cost and speed

- Model cost per question: about US$0.00017 (median 947 tokens in, 82 out, at US$0.10 and US$0.50 per million tokens). 200 questions a day for 30 days: about US$1 per shop and month, under the US$5 limit.
- All the course team's model calls for this report and the recordings: 435 calls, 0 errors, US$0.069.
- Search: about 9 ms (dense or hybrid) after the model is loaded; the first question of a process waits about 4 seconds for the model.

## Limitations

- 41 held-out questions: a difference of one or two questions is not evidence.
- The keys are regular expressions written by one person; at least one is too strict ("5–10" without spaces: Q46 on the tuning questions, Q45 in the baseline's second held-out pass). The keys were frozen before tuning and are not changed.
- Synthetic, short, clean documents. One laptop. One model (chat-small); the answers would differ with another model.
- The recorded answers make the numbers repeatable, but they are one sample of a model that does not always answer the same way (Q45).
