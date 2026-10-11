# Capstone: the document assistant (end of Module 4)

The journey is now safe and reliable: people sign in, each request is checked against the caller's membership in the shop, row-level security is a second lock, and the failure cases are handled: the wrong shop, a missing source, an invalid file and a slow model provider. Users can open the evidence behind a citation and delete what they uploaded.

## First run

```sh
python3 -m venv .venv && source .venv/bin/activate      # Windows: py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                                     # then change the password
python -m idp init                                       # the practice identity provider's keys; two secrets go into .env
docker compose up -d db
python -m scripts.load_pack
python -m scripts.failure_cases                          # the four failure cases, for real
python -m pytest
```

Then `python -m idp` in one terminal and `fastapi dev doc_assistant/main.py` in another, and sign in at http://127.0.0.1:8000 as Sam, Ines, Omar, Camille or Tomás (no password: practice only).

## What Module 4 added

- Sign-in (`idp/`, `doc_assistant/auth.py`, `login.py`): the authentication course's practice provider, token checks, a signed session cookie with a CSRF token.
- Access (`access.py`, `deps.py`, `migrations/002_row_level_security.sql`): memberships and roles, 404 for outsiders, 403 for a role that is too small, staff-only documents hidden from read-only members.
- Failure handling: bounded retries and timeouts (`providers.py`), refused files (413, 415, 422), failed parsing with a reason, duplicate-safe ingestion (`migrations/003_duplicate_safe_ingestion.sql`), `scripts/fake_provider.py` and `scripts/failure_cases.py`.
- Review and cleanup: the evidence view, deletion of a document with its passages, vectors and answers, and prompt v2 (passages are data, not instructions).

## Reset

`python -m scripts.load_pack --reset`; `python -m idp init --force` makes new keys and secrets.
