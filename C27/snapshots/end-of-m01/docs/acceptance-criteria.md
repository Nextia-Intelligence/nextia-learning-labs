# Acceptance criteria: the document assistant

Written by Sam with Grace (the user) in Module 1, before any code. Every criterion is testable, and each one names how it is checked.

## Required behaviour

| ID | Given | When | Then |
|---|---|---|---|
| B1 | a signed-in member of a shop | they ask a question that the shop's documents answer | they get a short answer, and every claim cites a passage of their own shop's documents |
| B2 | a signed-in member | they ask a question that the documents do not answer | the answer says that the documents do not answer it, and cites nothing |
| B3 | two versions of a policy | a question names a date | the answer uses the version in force on that date |
| B4 | a member who may upload | they upload a .md, .txt, .html or .pdf file of at most 5 MB | they see its status move from uploaded to indexed, or to failed with a reason they can act on |
| B5 | the same file | it is uploaded twice | there is one document, and the second upload says so |
| B6 | a member who may delete | they delete a document | its file, passages, vectors and the stored answers that cite it are gone, and no later answer uses it |
| B7 | the model provider is slow or down | a member asks a question | they get a clear error within 10 seconds of the last attempt, and nothing half-done is stored |
| B8 | any answer | the member clicks a citation | they see the passage, its document, version and dates |

## Quality thresholds

Measured on the held-out questions only (Module 5). Written before any measurement.

| ID | Measure | Threshold | Why this number |
|---|---|---|---|
| Q1 | correct answers on answerable held-out questions | at least 75% | the RAG course's assistant reached about 85% on similar questions; staff check every answer anyway |
| Q2 | abstains on questions the documents do not answer (also another shop's questions) | 100% | a confident wrong answer is worse than "no answer" for Grace |
| Q3 | citation validity (every cited passage exists in this shop and was given to the model) | 100% | code can check it fully, so anything less is a bug |
| Q4 | follows an instruction hidden in a document | 0 times | the supplier notes contain one on purpose |
| Q5 | median time from question to answer, on a laptop | under 5 seconds | the customer is waiting on the phone |

## Access control

| ID | Rule | Checked by |
|---|---|---|
| A1 | a member of one shop never receives another shop's documents, passages or answers | `python -m scripts.isolation`: 0 leaks |
| A2 | someone who is not a member gets the same "not found" for a real and a made-up shop | the access tests |
| A3 | a read-only member never receives a staff-only passage, and cannot upload or delete | the access tests and the isolation checks |
| A4 | every request that changes data from the page needs the CSRF token | the sign-in tests |

## Budget

| ID | Limit | Value |
|---|---|---|
| C1 | model cost per question | under US$0.001 |
| C2 | model cost per shop and month (enforced) | US$5, and 200 questions a day |
| C3 | money for building and evaluating the whole project | at most US$2 of model calls; no cloud resources |
