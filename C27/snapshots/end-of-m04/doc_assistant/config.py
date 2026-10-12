"""Settings from environment variables (and the project's .env file). One place, read once.

Secrets (the database password inside DATABASE_URL, LLM_API_KEY, OIDC_CLIENT_SECRET,
SESSION_SECRET) are fields with repr=False: printing the settings never shows them.
"""

import os
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def _bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default="", repr=False)
    # The assistant's answers: mock (made from the passages, no model), recorded (the course team's
    # recorded answers, mock for any other question) or live (an OpenAI-compatible endpoint)
    answer_provider: str = "recorded"
    answer_model: str = "chat-small"
    llm_base_url: str = ""
    llm_api_key: str = field(default="", repr=False)
    provider_timeout_s: float = 20.0
    provider_retries: int = 2            # extra attempts after a timeout, a 429 or a 5xx
    # Retrieval: the question's vector against every chunk's vector (dense search)
    top_k: int = 5
    prompt_version: str = "answer_v2"
    embedder: str = "e5"                 # e5 (the RAG course's model) or hash (tests only)
    torch_threads: int = 2
    # Ingestion
    max_upload_bytes: int = 5_000_000
    ingest_worker: str = "thread"        # thread (inside the API) or off (run python -m doc_assistant.worker)
    # Identity (Module 4)
    auth_mode: str = "oidc"              # oidc, or dev (one fixed user, Module 3 only)
    dev_user: str = "usr-sam"
    oidc_issuer: str = "http://localhost:8400"
    oidc_internal_url: str = ""
    oidc_audience: str = "doc-assistant"
    oidc_client_id: str = "doc-assistant-web"
    oidc_client_secret: str = field(default="", repr=False)
    session_secret: str = field(default="", repr=False)
    session_cookie_secure: bool = True
    public_url: str = "http://127.0.0.1:8000"
    app_db_role: str = "assistant_app"   # row-level security applies to this role
    app_version: str = "1.0.0"
    trace_file: str = "traces/spans.jsonl"
    today: str = ""                      # ASSISTANT_TODAY: the course's "today"; empty = the real date

    def today_date(self) -> str:
        return self.today or date.today().isoformat()


def load_env_file(path: Path | None = None) -> None:
    """Read KEY=value lines from .env (variables already set in the environment win)."""
    path = path or PROJECT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def from_env(env: dict | None = None) -> Settings:
    e = env if env is not None else os.environ
    s = Settings()

    def get(name: str, default):
        return e.get(name, default) or default

    return Settings(
        database_url=get("DATABASE_URL", s.database_url),
        answer_provider=get("ANSWER_PROVIDER", s.answer_provider),
        answer_model=get("ANSWER_MODEL", s.answer_model),
        llm_base_url=get("LLM_BASE_URL", s.llm_base_url),
        llm_api_key=get("LLM_API_KEY", s.llm_api_key),
        provider_timeout_s=float(get("PROVIDER_TIMEOUT_S", s.provider_timeout_s)),
        provider_retries=int(get("PROVIDER_RETRIES", s.provider_retries)),
        top_k=int(get("TOP_K", s.top_k)),
        prompt_version=get("PROMPT_VERSION", s.prompt_version),
        embedder=get("EMBEDDER", s.embedder),
        torch_threads=int(get("TORCH_THREADS", s.torch_threads)),
        max_upload_bytes=int(get("MAX_UPLOAD_BYTES", s.max_upload_bytes)),
        ingest_worker=get("INGEST_WORKER", s.ingest_worker),
        auth_mode=get("AUTH_MODE", s.auth_mode),
        dev_user=get("DEV_USER", s.dev_user),
        oidc_issuer=get("OIDC_ISSUER", s.oidc_issuer),
        oidc_internal_url=get("OIDC_INTERNAL_URL", s.oidc_internal_url),
        oidc_audience=get("OIDC_AUDIENCE", s.oidc_audience),
        oidc_client_id=get("OIDC_CLIENT_ID", s.oidc_client_id),
        oidc_client_secret=get("OIDC_CLIENT_SECRET", s.oidc_client_secret),
        session_secret=get("SESSION_SECRET", s.session_secret),
        session_cookie_secure=_bool(get("SESSION_COOKIE_SECURE", "true")),
        public_url=get("PUBLIC_URL", s.public_url).rstrip("/"),
        app_db_role=get("APP_DB_ROLE", s.app_db_role),
        app_version=get("APP_VERSION", s.app_version),
        trace_file=get("TRACE_FILE", s.trace_file),
        today=get("ASSISTANT_TODAY", s.today),
    )


@lru_cache
def settings() -> Settings:
    load_env_file()
    return from_env()
