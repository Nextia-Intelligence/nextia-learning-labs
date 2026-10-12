"""What the scripts share: the settings, the database, the models and a caller (no server needed).

The scripts call the same code as the API (the pipeline, the ingestion, the worker) inside one
process. A script acts as a person of the identity data, through that person's membership, so
the same checks apply as in the API.
"""

from doc_assistant import tracing
from doc_assistant.access import Principal, membership
from doc_assistant.config import settings as load_settings
from doc_assistant.db import Database
from doc_assistant.embed import make_embedder
from doc_assistant.pipeline import Deps
from doc_assistant.providers import make_provider

# Who the scripts act as in each shop: an owner or staff member, and a read-only member.
STAFF = {"larkfield": "usr-sam", "bramble": "usr-ines"}
READ_ONLY = {"larkfield": "usr-omar", "bramble": "usr-camille"}


def open_deps(settings=None, provider=None) -> Deps:
    s = settings or load_settings()
    if not s.database_url:
        raise SystemExit("Set DATABASE_URL in .env (copy .env.example).")
    tracing.setup(s.trace_file, s.app_version)
    db = Database(s.database_url, s.app_db_role)
    db.open()
    return Deps(db, s, make_embedder(s.embedder, s.torch_threads), provider or make_provider(s))


def as_member(deps: Deps, user_id: str, tenant: str) -> Principal:
    with deps.db.admin() as conn:
        return membership(conn, user_id, tenant)
