# Marking rubric for the final assignment

The final assignment: build a synthetic document support assistant with ingestion, grounded answers, citations, two-tenant access control and an evaluation report. Each required item is marked **demonstrated**, **partially demonstrated** or **not yet demonstrated**, always with a concrete reason. The course is complete when every item is demonstrated; you may revise and submit again.

A working happy path is not enough: if a taught access-control, data-integrity or irreversible-action check fails, the item it belongs to is **not yet demonstrated**, however good the rest is.

## 1. Working user journey

| Mark | What the reviewer sees |
|---|---|
| Demonstrated | A new user signs in, uploads a document, sees it move to indexed (or to failed with a reason), asks a question and gets an answer whose claims cite passages of their own documents; clicking a citation shows the passage. A question the documents do not answer gets a clear "no answer". |
| Partially demonstrated | The journey works, but one state is missing or unclear: no visible indexing status, errors shown as raw text or stack traces, citations that cannot be opened, or a "no answer" that looks like an answer. |
| Not yet demonstrated | The journey does not work from the README's steps, or it needs steps that are not written down, or answers have no citations. |

## 2. Reproducible repository and deployment

| Mark | What the reviewer sees |
|---|---|
| Demonstrated | On a clean computer, the README's steps start the product (a local Compose demonstration is enough), the tests pass, the smoke test passes, and a reset path is written. Versions are pinned. No secret is in the repository. A CI workflow runs the tests. |
| Partially demonstrated | It runs, but the reviewer had to fix one thing (a missing step, an unpinned package, a port) or the CI workflow does not run the tests. |
| Not yet demonstrated | It does not start from the README, or a secret (a key, a password that is not an example) is committed. |

## 3. Held-out evaluation and isolation checks

| Mark | What the reviewer sees |
|---|---|
| Demonstrated | The held-out questions were reserved before tuning (a lock or a commit before any tuning), cover every kind of question, and were run once per compared version. The report gives retrieval, answer correctness, citation validity, abstention, injection and cost, with failures shown. Wrong-shop isolation checks were run on retrieval, the API and the database, with 0 leaks. |
| Partially demonstrated | The numbers are there, but the held-out set was changed after tuning, or the report shows only successes, or the isolation checks cover only one layer. |
| Not yet demonstrated | No held-out set, or any isolation check finds a leak, or the numbers cannot be reproduced from the repository. |

## 4. Clear demo, architecture and limitations

| Mark | What the reviewer sees |
|---|---|
| Demonstrated | A five-minute demo (live or recorded) shows the user problem, the working flow, one failure case and one design trade-off with its evidence. The architecture shows the trust boundaries and where each shop's data is separated. The limitations are specific and honest, and completed work is separated from planned extensions. The learner can explain any part of the code when asked. |
| Partially demonstrated | The demo skips the failure case or the trade-off, or the limitations are generic ("could be improved"). |
| Not yet demonstrated | Claims without evidence (for example "production-ready", "secure", employment or user claims), real private documents in a public demo, or the learner cannot explain their own decisions. |

## Optional extension (only after items 1 to 4 are demonstrated)

A custom model, an agent or an MCP integration, with its own evidence. It is never marked instead of a required item.
