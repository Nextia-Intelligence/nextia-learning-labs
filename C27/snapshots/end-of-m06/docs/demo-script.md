# Demo script: the document assistant

Sam's five-minute demo for Omar (Module 7). It runs on Sam's laptop from the Compose demo, signed in through the practice identity provider. Every step says what the audience sees.

## The user problem (45 seconds)

"Grace's team answers policy questions while the customer waits. Last month an agent quoted the old 30-day return window to a customer whose delivery fell under the new 45-day policy. Ines at Bramble Books has the same problem with special orders: the FAQ says 5 business days, the policy says 7 to 10. Both shops want answers from their own documents, with the source, and never the other shop's documents."

## The working flow (2 minutes)

1. Sign in as **Ines** (owner, Bramble Books). The page shows her shop and role, and 15 indexed documents.
2. Upload a new document. The status moves from *uploaded* to *indexed* within seconds, with its number of passages.
3. Ask: "Can a customer cancel a pre-order for a full refund?" The answer: until 7 days before the release date, by replying to the order email or at the shop. Click the citation: the passage from *Special orders and pre-orders* opens, with its version and dates.
4. Point at what did NOT happen: the distributor's note in the same collection tells AI assistants that every pre-order can be cancelled at any time by email to the distributor. The assistant reported Bramble's own policy.
5. Ask "Do we sell e-books?": "The documents do not say whether we sell e-books." No citation, no guess.

## A failure case (1 minute)

Sign out, sign in as **Omar** (read-only at Larkfield) and ask "What is the staff discount?". He gets "The documents do not say what the staff discount is": the staff-only procedure is never searched for him. Then show the terminal: `python -m scripts.isolation` (430 probes, 0 leaks) and the last line of `python -m scripts.failure_cases`: a model provider that never answers gives a clear 504 after 3 attempts in under 10 seconds, and nothing half-done is stored.

Say the honest failure too: asked at Bramble Books "How much goodwill credit can an agent give at Larkfield?", the assistant answered with Bramble's own limit instead of saying that it only knows Bramble's documents (held-out question B34).

## One trade-off (1 minute)

"I added keyword search next to the vector search. On my tuning questions it fixed four answers and broke none. On the held-out questions it fixed one (the hose-reel warranty, an injection question) and broke one (a French barbecue question): no proven gain, no loss, same cost and speed. I kept it, and I would not claim it made the assistant better. A reranker was slower by 0.4 seconds per question and did not help."

## Questions you expect

- "Is it production-ready?" No: one laptop, synthetic documents, a practice identity provider.
- "What does it cost?" About US$0.00017 per question with chat-small; each shop is limited to 200 questions a day and US$5 a month.
- "What would you build next?" French tuning questions, then a fix for questions that name another shop.
