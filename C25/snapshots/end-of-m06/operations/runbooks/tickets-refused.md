# Runbook: tickets are refused

**Alert:** `accept-fast-burn` (SEV-2; SEV-1 if no ticket is accepted). **Owner:** Amira.

## Detection

- More than 1.44% of ticket requests answered 5xx in 5 minutes (14.4 times the budget).

## Triage

1. Which error? `503 queue_full` (the queue bound), `503 database_busy` (the pool), or 5xx
   from the API itself. The `error.code` is in the API's answer and logs.
2. Is the database up? `docker compose ps db`, `GET /ready`.

## Mitigation

- `queue_full`: more workers if the provider has room; else keep the bound (it protects the
  service) and tell customers the wait.
- The database: see the databases course's runbooks (connections, disk, restore).

## Recovery checks

- [ ] The accept SLI is back above 99.9% over the last 15 minutes.
- [ ] Customers who were refused got a reply (Grace's team).
