"""The document assistant's API and its page.

    fastapi dev doc_assistant/main.py         on your computer (reloads when a file changes)
    fastapi run doc_assistant/main.py         as in the container

At start-up: open the database pool, load the embedding model (and the reranker), choose the
answer provider, and start the ingestion worker thread. /health says the process runs;
/ready says it can serve (the database answers and every migration is applied).
"""

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import __version__, answers, documents, errors, login, tracing
from .auth import make_validator
from .config import settings as load_settings
from .db import Database
from .embed import make_embedder
from .migrate import MIGRATIONS
from .providers import make_provider
from .rerank import make_reranker
from .worker import WorkerThread

logger = logging.getLogger("doc_assistant")
access_log = logging.getLogger("doc_assistant.access")
STATIC = Path(__file__).resolve().parent / "static"


def create_app(settings=None, start_worker: bool | None = None) -> FastAPI:
    s = settings or load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        tracing.setup(s.trace_file, s.app_version)
        db = Database(s.database_url, s.app_db_role)
        db.open()
        app.state.db = db
        app.state.embedder = make_embedder(s.embedder, s.torch_threads)
        app.state.reranker = make_reranker(s.embedder, s.torch_threads) if s.retrieval_mode.endswith("_rerank") else None
        app.state.provider = make_provider(s)
        app.state.validator = make_validator(s)
        if s.auth_mode == "dev":
            logger.warning("AUTH_MODE=dev: every request without a token acts as %s. Use it only on your computer.",
                           s.dev_user)
        worker = None
        if start_worker if start_worker is not None else s.ingest_worker == "thread":
            worker = WorkerThread(db, app.state.embedder)
            worker.start()
        yield
        if worker:
            worker.close()
        db.close()

    app = FastAPI(title="Document assistant", version=__version__, lifespan=lifespan,
                  description="Answers from each shop's own documents, with citations.")
    app.state.settings = s
    errors.install(app)

    @app.middleware("http")
    async def request_log(request: Request, call_next):
        request.state.request_id = uuid.uuid4().hex[:16]
        start = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        if request.url.path.startswith(("/v1/", "/auth/")):
            response.headers["Cache-Control"] = "no-store"
        access_log.info(json.dumps({
            "request_id": request.state.request_id, "method": request.method, "path": request.url.path,
            "status": response.status_code, "ms": round((time.monotonic() - start) * 1000, 1),
            "tenant": getattr(request.state, "tenant", None), "user": getattr(request.state, "user_id", None)}))
        return response

    @app.get("/health", tags=["operations"])
    def health():
        return {"status": "ok", "version": s.app_version}

    @app.get("/ready", tags=["operations"])
    def ready(request: Request):
        problems = []
        try:
            with request.app.state.db.admin() as conn:
                applied = {r["version"] for r in conn.execute("SELECT version FROM schema_migrations").fetchall()}
            missing = sorted(p.stem for p in MIGRATIONS.glob("*.sql") if p.stem not in applied)
            if missing:
                problems.append(f"migrations not applied: {', '.join(missing)}")
        except Exception:  # noqa: BLE001 - not ready, whatever the reason
            problems.append("the database does not answer")
        if problems:
            raise errors.ApiError(503, "not_ready", "; ".join(problems))
        return {"status": "ready", "version": s.app_version, "answer_provider": s.answer_provider,
                "retrieval_mode": s.retrieval_mode, "auth_mode": s.auth_mode}

    @app.get("/v1/me", tags=["identity"])
    def me(request: Request):
        who = login.identify(request)
        with request.app.state.db.admin() as conn:
            user = conn.execute("SELECT user_id, name, email FROM users WHERE user_id = %s", (who.user_id,)).fetchone()
            shops = conn.execute("SELECT m.tenant_id, t.name, m.role FROM memberships m JOIN tenants t"
                                 " USING (tenant_id) WHERE m.user_id = %s ORDER BY t.name", (who.user_id,)).fetchall()
        return {"user": user or {"user_id": who.user_id}, "via": who.via, "memberships": shops}

    @app.get("/", include_in_schema=False)
    def home():
        return RedirectResponse("/app/")

    app.include_router(login.router, tags=["identity"])
    app.include_router(documents.router, tags=["documents"])
    app.include_router(answers.router, tags=["answers"])
    app.mount("/app", StaticFiles(directory=STATIC, html=True), name="app")
    return app


logging.basicConfig(level=logging.INFO, format="%(message)s")
app = create_app()
