# Architecture and contracts: <your product's name>

Write this in Module 2 (*Architecture and contracts*), before you build any integration.

## Components

<A diagram (Mermaid or draw.io) and one line per component: what it does, and what it must never do.>

## Contracts

| Method and path | Who may call it | Request | Success | Errors |
|---|---|---|---|---|
| <POST /v1/tenants/{tenant}/answers> | <members of the shop> | <{"question": ...}> | <200 {answer, claims, ...}> | <401, 404, 422, 504> |

## Data model

<The tables, their keys, and which column says which shop a row belongs to.>

## Ingestion states

<uploaded -> parsing -> indexed / failed: what moves a document from one state to the next, and what the user sees in each.>

## Retrieval metadata

<What each chunk carries (shop, document, version, dates, access level, section) and which filter uses it.>
