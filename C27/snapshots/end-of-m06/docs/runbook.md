# Runbook: rollback, cleanup and usage limits

Module 6. What to do when a release goes wrong, how to remove everything, and how the usage limits protect the budget.

## Roll back a release

A release is an image tag (`doc-assistant:<version>`) plus its settings. Keep the previous tag until the new one has passed the smoke test.

```sh
APP_VERSION=1.0.1 docker compose --profile app up -d --wait     # the new release
SMOKE_TOKEN=$(python -m idp token usr-sam) python scripts/smoke.py http://127.0.0.1:8000
# if the start or the smoke test fails:
APP_VERSION=1.0.0 docker compose --profile app up -d --wait     # back to the previous tag and settings
SMOKE_TOKEN=$(python -m idp token usr-sam) python scripts/smoke.py http://127.0.0.1:8000
```

The rollback keeps the database. That is safe only if every migration of the new release is additive (new tables and columns that the old code ignores), as all five migrations here are. A release that removes or renames a column needs two releases (expand, then contract), as the CI/CD course teaches.

The drill, run by the course team on the course-end project (one laptop, other work running):

| Step | Result |
|---|---|
| Build `doc-assistant:1.0.0` (CPU torch and both models inside) | 107 s; image 1.11 GB |
| Start the stack (`up --wait`) | 9.7 s; the API container used about 820 MB of memory |
| Load the data pack inside the container | 15.7 s |
| Smoke test | 7 of 7 checks passed |
| "Release" 1.0.1 with `ANSWER_PROVIDER=live` and no `LLM_BASE_URL` (a constructed bad setting) | `up --wait` failed after 4.5 s: "container c27f-api-1 exited (3)"; the log says `ValueError: ANSWER_PROVIDER=live needs LLM_BASE_URL (and LLM_API_KEY).` and "Application startup failed"; the smoke test could not connect |
| Roll back to 1.0.0 with its settings | 7.5 s; smoke test 7 of 7 again; the data was still there (36 documents indexed) |

A release that fails at start is the easy case: readiness never turns green, so nothing new serves traffic. A release that starts and answers wrongly is found only by the smoke test and the evaluation, which is why both run before you call a release done.

## Usage limits

- `DAILY_QUESTION_LIMIT` (200) questions per shop per day, and `MONTHLY_BUDGET_USD` (5) of model cost per shop per month. Over a limit, a question gets 429 `limit_reached` with `Retry-After`; nothing is sent to the model.
- See a shop's usage: `GET /v1/tenants/{tenant}/usage`.
- Usage is kept per day in `usage_days`; deleting documents or answers does not reset it.

## Clean up everything

```sh
docker compose --profile app down --volumes            # containers, network and the database volume
docker image rm doc-assistant:1.0.0 doc-assistant:1.0.1 # your image tags (docker image ls doc-assistant)
docker image rm pgvector/pgvector:0.8.7-pg18-trixie     # if no other project uses it
rm -rf .venv .idp traces .env                           # Windows: Remove-Item -Recurse -Force .venv, .idp, traces, .env
```

The two models stay in the Hugging Face cache (about 1 GB, `~/.cache/huggingface`); delete them there if no other project uses them. If you ran the optional cloud steps: `az group delete --name <group> --yes`, then `az group exists --name <group>` must say `false`.
