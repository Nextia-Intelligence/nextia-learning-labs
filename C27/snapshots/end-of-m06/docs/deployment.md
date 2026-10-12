# Release the demo

Module 6. The demo runs on your computer, from the same image that CI builds and tests, and it is private: every port listens on 127.0.0.1 only. Show it on your screen, or record a video. A cloud deployment is optional; its steps are at the end, and the course team did not run them.

## The release, step by step

1. **Build once, test that build.** CI (`.github/workflows/ci.yml`) runs ruff, the held-out lock check, the tests with PostgreSQL, the isolation checks and an evaluation smoke test on the recorded answers. Then it builds the image, starts the whole stack and runs `scripts/smoke.py` against it. On your computer: `docker compose --profile app up -d --build --wait`.
2. **Tag the image with its version.** `APP_VERSION=1.0.0 docker compose --profile app build` makes `doc-assistant:1.0.0`. Keep the previous tag: it is your rollback (`docs/runbook.md`).
3. **Secrets stay outside the image.** `.env` and `.idp/` are in `.dockerignore`. The containers get `POSTGRES_PASSWORD`, `OIDC_CLIENT_SECRET` and `SESSION_SECRET` from your `.env` through Compose; `python -m idp init` makes the last two. A live model's key (`LLM_API_KEY`) would come the same way, never from a file in the image.
4. **Migrations run before the API.** The `migrate` service runs `python -m doc_assistant.migrate` and must finish successfully before `api` starts.
5. **Health checks.** `/health` says the process runs (no database call: a liveness check). `/ready` says it can serve: the database answers and every migration is applied (a readiness check). Compose waits for `/ready` (`--wait`).
6. **Load the data, then smoke-test.** `docker compose --profile app run --rm api python -m scripts.load_pack`, then `SMOKE_TOKEN=$(python -m idp token usr-sam) python scripts/smoke.py http://127.0.0.1:8000`.
7. **Logs.** One JSON line per request (`docker compose --profile app logs api`): request ID, method, path, status, time, shop and user, never the question or a token. Every error body has the same request ID, so a user's screenshot leads to the log line. Traces of each question: `traces/spans.jsonl` in the container (`docker compose --profile app exec api python -m scripts.trace last`).

## What is private, and why

- Ports bind to 127.0.0.1: nobody else on your network can open the demo.
- The practice identity provider asks for no password: never expose it.
- `SESSION_COOKIE_SECURE=false` is only for http on your own computer. Anywhere else, use https and leave it at `true`.

## Optional: the cloud (written, not run by the course team)

The containers and CI/CD courses ran Azure Container Apps for real; follow them for each step. For this project you would need, in one resource group with tags `purpose=practice`:

1. Azure Database for PostgreSQL flexible server (Burstable B1ms), with the `vector` extension allowed (`azure.extensions = VECTOR`), private access or a firewall rule for the app only. Run the migrations as the administrator: migration 002 grants the role `assistant_app` to it.
2. The image in a registry (GHCR, as in the CI/CD course), referenced by digest.
3. A Container Apps environment and one app: 1 vCPU and 2 GiB (the two models need about 1 GB of memory), minimum 1 replica (the models take seconds to load, so a cold start would make the first question slow), ingress on port 8000, the liveness probe on `/health` and the readiness probe on `/ready`.
4. Secrets as Container Apps secrets (`DATABASE_URL`, `SESSION_SECRET`, `OIDC_CLIENT_SECRET`), referenced with `secretref:`.
5. A real identity provider instead of the practice one (the authentication course tested Keycloak and described Microsoft Entra ID): set `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` and `PUBLIC_URL` (https), and keep `SESSION_COOKIE_SECURE=true`.
6. The same smoke test against the app's URL, then **delete the resource group the same day** (`az group delete --name <group> --yes`, then `az group exists` must say `false`).

Cost: check the price pages before you start. The system design course priced a similar design (one always-on replica and a small PostgreSQL server) at about US$50 a month for two shops; for a one-day demo it is a few dollars, if you delete it.
