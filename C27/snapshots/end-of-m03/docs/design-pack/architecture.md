# Architecture and contracts

Sam's design pack, Module 2. Reviewed by Kwame (architecture) and Mei (ingestion and deletion) before any integration was built.

## Components

```mermaid
flowchart LR
  subgraph browser["Browser (one plain page)"]
    page["/app/ page<br/>upload, status, question, answer, evidence"]
  end
  subgraph local["Your computer (Docker Compose)"]
    idp["Practice identity provider<br/>sign-in, tokens (RS256)"]
    subgraph api["API process (FastAPI)"]
      routes["Routes<br/>validate, identify, check membership"]
      pipeline["Answer pipeline<br/>retrieve, assemble, generate, check, store"]
      worker["Ingestion worker (thread)<br/>parse, chunk, embed"]
      models["Local models (CPU)<br/>e5-small embeddings, cross-encoder"]
    end
    db[("PostgreSQL + pgvector<br/>documents, files, chunks, vectors,<br/>answers; row-level security")]
  end
  provider["Model provider<br/>recorded answers by default,<br/>or a live endpoint"]
  page -- "cookie session (same origin)" --> routes
  page -. "sign-in redirect" .-> idp
  routes -- "keys (JWKS)" --> idp
  routes --> pipeline --> db
  routes --> db
  worker --> db
  pipeline --> models
  worker --> models
  pipeline -- "question + passages only" --> provider
```

| Component | Its one job | It must never |
|---|---|---|
| Page | let a member upload, follow the status, ask, read the evidence | put server text on the page as HTML; keep a token |
| Routes | check the request, the caller and their membership; call one service | trust a shop or a role sent by the browser |
| Answer pipeline | turn one question into a stored, cited answer | search another shop; send anything but the question and the passages to the model |
| Ingestion worker | index uploaded documents, one at a time | lose a document: a failure ends as `failed` with a reason |
| PostgreSQL | keep every shop's data, separated by `tenant_id` and row-level security | let a query of one shop see another shop's rows |
| Model provider | write an answer from the passages | receive a document that the caller may not read |

## Contracts

All paths of shop data start with `/v1/tenants/{tenant}`. The shop in the path is only a request: the membership decides. Every error has one shape: `{"code", "message", "request_id"}` (+ `details` for a validation error).

| Method and path | Who may call it | Request | Success | Errors |
|---|---|---|---|---|
| `POST /v1/tenants/{t}/documents` | owner, staff | multipart: `file`; optional `access`, `version`, `title`, `effective_from`, `effective_to`, `doc_key`, `doc_type` | 202 `{document, duplicate: false}` + `Location`; 200 `{document, duplicate: true}` for the same file again | 401, 403, 404, 409 `conflict`, 413 `file_too_large`, 415 `unsupported_file`, 422 |
| `GET /v1/tenants/{t}/documents` | every member | | 200 `{documents, counts}` (read-only members see public documents only) | 401, 404 |
| `GET /v1/tenants/{t}/documents/{id}` | every member | | 200 `{document}` with `status`: uploaded, parsing, indexed or failed (+ `error`) | 401, 404 |
| `DELETE /v1/tenants/{t}/documents/{id}` | owner, staff | | 200 `{deleted: {chunks, answers}}` | 401, 403, 404 |
| `POST /v1/tenants/{t}/answers` | every member | `{"question": 3-500 characters, "as_of": "YYYY-MM-DD" (optional)}` | 200 `{answer: {answerable, answer, claims: [{text, citations, problems}], passages, needs_review, provider, model, tokens, cost_usd, latency_ms, trace_id}}` | 401, 404, 422, 429 `limit_reached`, 502 `provider_bad_answer`, 503 `provider_unavailable`/`provider_busy`, 504 `provider_timeout` |
| `GET /v1/tenants/{t}/answers`, `/answers/{id}` | the member who asked | | 200 | 401, 404 |
| `GET /v1/tenants/{t}/chunks/{chunk_id}` | every member (access level applies) | | 200 `{chunk}`: the evidence behind a citation | 401, 404 |
| `GET /v1/me` | anyone signed in | | 200 `{user, memberships}` | 401 |
| `GET /health`, `GET /ready` | anyone | | 200 | 503 `not_ready` |

## Data model

Every table with shop data has `tenant_id`, and every key that points at another row includes it (a chunk cannot belong to another shop's document). Migrations: `001_core.sql` (this module), then `002` row-level security, `003` duplicate-safe ingestion, `004` keyword search, `005` usage limits.

```mermaid
erDiagram
  tenants ||--o{ memberships : has
  users ||--o{ memberships : has
  tenants ||--o{ documents : owns
  documents ||--|| document_files : "bytes"
  documents ||--o{ chunks : "passages + vectors"
  tenants ||--o{ answers : owns
  documents {
    uuid document_id
    text tenant_id
    text doc_key
    text version
    text access "public or staff"
    date effective_from
    date effective_to
    text status "uploaded, parsing, indexed, failed"
    text sha256
  }
  chunks {
    text tenant_id
    text chunk_id
    uuid document_id
    text section
    vector embedding "384"
  }
  answers {
    uuid answer_id
    text tenant_id
    text user_id
    jsonb citations
    uuid[] cited_documents
    numeric cost_usd
  }
```

## Ingestion states

```mermaid
stateDiagram-v2
  [*] --> uploaded: upload accepted (202)
  uploaded --> parsing: the worker claims it (lease 5 minutes)
  parsing --> indexed: parsed, chunked, embedded, saved in one transaction
  parsing --> failed: the file cannot be parsed (at once, with the reason)
  parsing --> uploaded: another error (tried again, at most 3 attempts)
  parsing --> parsing: the lease ended (a worker died): claimed again
  indexed --> [*]: deleted (file, chunks, vectors, answers)
  failed --> [*]: deleted
```

What the user sees: `uploaded` and `parsing` as "indexing" (the page asks again every 1.5 seconds), `indexed` with the number of passages, `failed` with the reason ("This file is not a readable PDF").

## Retrieval metadata

Each chunk is one section of one document version (the RAG course's structure chunker), and starts with the document title. The search filters BEFORE taking the top 5: the shop (`tenant_id`), the access level (a read-only member gets public documents only), the date (`effective_from <= as_of <= effective_to`), and the embedding model (`documents.embedder`). Each passage given to the model has a header: `[chunk_id] title | type, version, in force from ... to ... | section`.
