"""What the scripts share: the settings, the database, the models and a caller (no server needed).

The scripts call the same code as the API (the pipeline, the ingestion, the worker) inside one
process. A script acts as a person of the identity data.
"""

from doc_assistant import tracing
from doc_assistant.access import Principal
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
    db = Database(s.database_url)
    db.open()
    return Deps(db, s, make_embedder(s.embedder, s.torch_threads), provider or make_provider(s))


def as_member(deps: Deps, user_id: str, tenant: str) -> Principal:
    """Module 3: no membership check yet (Module 4 adds it); the shop must exist."""
    with deps.db.admin() as conn:
        shop = conn.execute("SELECT name FROM tenants WHERE tenant_id = %s", (tenant,)).fetchone()
        user = conn.execute("SELECT name FROM users WHERE user_id = %s", (user_id,)).fetchone()
    if shop is None:
        raise SystemExit(f"No shop {tenant}.")
    return Principal(user_id, user["name"] if user else user_id, tenant, shop["name"], "staff")
