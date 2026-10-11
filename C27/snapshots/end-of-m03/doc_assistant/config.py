"""Settings from environment variables (and the project's .env file). One place, read once.

Secrets (the database password inside DATABASE_URL, LLM_API_KEY) are fields
with repr=False: printing the settings never shows them.
"""

import os
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


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
    # Retrieval: the question's vector against every chunk's vector (dense search)
    top_k: int = 5
    prompt_version: str = "answer_v1"
    embedder: str = "e5"                 # e5 (the RAG course's model) or hash (tests only)
    torch_threads: int = 2
    # Ingestion
    max_upload_bytes: int = 5_000_000
    ingest_worker: str = "thread"        # thread (inside the API) or off (run python -m doc_assistant.worker)
    # Identity: Module 4 adds the sign-in; until then every request acts as one practice user
    auth_mode: str = "dev"
    dev_user: str = "usr-sam"
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
        top_k=int(get("TOP_K", s.top_k)),
        prompt_version=get("PROMPT_VERSION", s.prompt_version),
        embedder=get("EMBEDDER", s.embedder),
        torch_threads=int(get("TORCH_THREADS", s.torch_threads)),
        max_upload_bytes=int(get("MAX_UPLOAD_BYTES", s.max_upload_bytes)),
        ingest_worker=get("INGEST_WORKER", s.ingest_worker),
        auth_mode=get("AUTH_MODE", s.auth_mode),
        dev_user=get("DEV_USER", s.dev_user),
        app_version=get("APP_VERSION", s.app_version),
        trace_file=get("TRACE_FILE", s.trace_file),
        today=get("ASSISTANT_TODAY", s.today),
    )


@lru_cache
def settings() -> Settings:
    load_env_file()
    return from_env()
