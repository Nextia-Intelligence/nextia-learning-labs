# Threat and cost review

Sam's review, Module 2, with Kwame (architecture and budget) and Mei (data and deletion). It uses the AI security course's method: draw the trust boundaries, list what crosses them, and name a check and a test for each threat.

## Trust boundaries

| Boundary | What crosses it | What we check there |
|---|---|---|
| Browser -> API | session cookie or access token; the shop in the path; questions; uploaded files | the token's signature, issuer, audience and expiry (or the signed cookie and its CSRF token); the membership of that shop; the request's shape and size; the file's type and size |
| API -> database | queries of one shop | every query names the shop; row-level security as a second lock (a transaction runs as `assistant_app` with `app.tenant_id`) |
| Document -> model | passages inside the prompt | the passages are data, not instructions (prompt rule); only passages the caller may read; the citations are checked in code afterwards |
| API -> model provider | the question and the passages, nothing else | no user ID, no email, no other shop's text; a timeout and bounded retries; recorded answers by default |
| Identity provider -> API | the provider's public keys | fetched from the configured issuer only; RS256 only |

## Threats

| Threat | Example | Mitigation | Test |
|---|---|---|---|
| Another shop's data | Ines changes `larkfield` to `bramble` in the URL; a Bramble document ID through Larkfield's path | membership check on every request (404 for non-members); `tenant_id` in every query and key; row-level security | `scripts/isolation.py` (0 leaks); `tests/test_access.py` |
| A staff-only procedure shown to the wrong person | a read-only member asks "What is the staff discount?" | the access level is filtered before the top 5; the evidence view and citation lookup apply it too | `tests/test_access.py`; the isolation checks |
| An instruction hidden in a document | the supplier notes tell "AI assistants" to promise a lifetime warranty | prompt rule 6 (passages are data); document type shown in every passage header; a policy rule that supplier content never changes a policy | the injection-bait questions (must be 0 obeyed) |
| A made-up or borrowed citation | the model cites an ID it did not see, or another shop's chunk | every citation is looked up in this shop at the caller's level and checked against the passages it was given | citation validity = 100%; `tests/test_answers_unit.py` |
| A file that breaks ingestion | a PDF cut during the upload; a 50 MB file; a Word file | size limit (5 MB) and type check at upload; parse errors end as `failed` with a reason; other errors are retried at most 3 times | `tests/test_failures.py`, `tests/test_ingest.py`; `scripts/failure_cases.py` |
| Material that should be gone | a deleted policy still answers questions, or its text stays in stored answers | deletion removes the file, chunks, vectors and the answers that cite it, in one transaction | `tests/test_deletion.py` |
| A bill that grows | a script asks thousands of questions | a daily question limit and a monthly model budget per shop (Module 6) | `tests/test_operations.py` |
| Cross-site requests from the browser | another site posts to the API with the user's cookie | SameSite=Lax cookie; CSRF token on every request that changes data | `tests/test_auth.py` |
| Secrets in the repository | a key committed by mistake | `.env` and `.idp/` are git-ignored; keys are read from the environment only; settings never print them | review; CI does not need any secret |

Accepted risks (written down, not fixed): the session cookie cannot be revoked before it expires (8 hours) — removing a membership takes effect at once, because membership is read on every request; the practice identity provider is not a real one; response times may differ slightly between a real and a made-up document ID.

## Tenant isolation rules

1. Every table with shop data has `tenant_id`; every key that points at another row includes it (composite foreign keys).
2. The shop comes from the path, and only a membership of the caller in that shop makes it valid. A token or a cookie never carries a shop or a role.
3. Every query has `tenant_id = %s`, and every shop transaction runs under row-level security as well.
4. Retrieval filters by shop, access level, date and model before the top k.
5. A citation is looked up again in the caller's shop at the caller's access level before it is shown.
6. The same document key in two shops is two documents; chunk IDs include the shop.
7. Errors never say whether something exists in another shop: 404 for "not yours" and "does not exist".

## Budget

| Resource | Limit | How it is enforced | Source of the number |
|---|---|---|---|
| Model cost per question | under US$0.001 | measured in Module 5 | first estimate: the RAG course measured US$0.00017 per question with chat-small (recorded) |
| Model cost per shop and month | US$5 | `MONTHLY_BUDGET_USD` refuses questions (429) when it is used up | assumption: 200 questions a day × US$0.00017 × 30 days ≈ US$1 |
| Questions per shop and day | 200 | `DAILY_QUESTION_LIMIT` | assumption: two small help desks |
| Building and evaluating the project | at most US$2 of model calls | logged per call in the course team's run log | the owner's rule |
| Cloud resources | none in the core | the demo runs in Docker Compose on a laptop | the course's rule; cloud steps are optional |
| Laptop | 16 GB of memory, one model process | two local models of about 470 MB each on the CPU, 2 threads | the course team's computer |
