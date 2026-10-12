"""Release manifests: one file that names every version that makes the service's answers
(the MLOps course, Module 2).

    operations/releases/<release ID>.toml

A manifest ties together the code (its version, Git commit, image digest and a fingerprint of
the code files), the database migrations, the assistant's prompt (file and fingerprint), the
output schema, the model (deployment and the model version we expect), the retrieval
settings, the evaluation set and its evidence, and the settings that change behaviour. The
release ID is the code version plus the first 6 characters of a hash of everything else:
change anything and you get a new ID.

The service reads its manifest at start (RELEASE_ID) and puts the release ID on every AI
result (ai_runs.release_id) and on its telemetry. So for any answer you can find the exact
versions that made it: python -m ops trace TICKET.

python -m ops release build writes a manifest; the release workflow runs it for each version.
"""

import hashlib
import json
import subprocess
import tomllib
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path

from ticket_api import ai, assistant

ROOT = Path(__file__).resolve().parents[1]
FOLDER = Path("operations/releases")
VERSION = "1.5.0"
# Files whose content is "the code": change one and the code fingerprint changes.
CODE_GLOBS = ("ticket_api/*.py", "simulator/*.py")
# Settings that change what the service does with a ticket (read when the manifest is built).
BEHAVIOUR = (
    "INTAKE_MODE",
    "PROVIDER_TIMEOUT",
    "PROVIDER_RETRIES",
    "JOB_MAX_ATTEMPTS",
    "BREAKER_FAILURES",
    "QUEUE_MAX",
    "CACHE_TTL_SECONDS",
)
# The evaluation course's set (its dataset card): the full file and its inputs only.
EVALUATION_SET = {"version": "d4c96eaa10c0", "inputs_version": "3f90ab808275", "cases": 271}


# The release that does the current request or job (the API sets it for each request, the
# worker for each job). Every AI result made in that request or job gets this ID.
CURRENT: ContextVar[str | None] = ContextVar("release_id", default=None)


class ReleaseError(ValueError):
    """The manifest is missing, or it does not match the files of the service."""


@dataclass(frozen=True)
class Release:
    id: str
    prompt: str
    prompt_fingerprint: str
    manifest: dict

    @property
    def expected_model_version(self) -> str:
        return self.manifest["model"]["expected_version"]


def sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def code_fingerprint(root: Path = ROOT) -> str:
    h = hashlib.sha256()
    for pattern in CODE_GLOBS:
        for path in sorted(root.glob(pattern)):
            h.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes())
    return h.hexdigest()[:12]


def migrations(root: Path = ROOT) -> list[str]:
    return sorted(p.name for p in (root / "migrations").glob("*.sql"))


def git_commit(root: Path = ROOT) -> str:
    """The Git commit of the project, if the project folder is a Git repository."""
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True
        )
        if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root.resolve():
            return "none (the project folder is not a Git repository)"
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True
        )
        dirty = subprocess.run(
            ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True
        ).stdout.strip()
        return head.stdout.strip() + (" (with changes not committed)" if dirty else "")
    except OSError:
        return "none (Git is not installed)"


def build(
    prompt: str,
    *,
    expected_model_version: str = "gpt-6-luna-2026-09-22",
    image: str = "not built (the course runs the service with Python)",
    evidence: str = "",
    index_version: str = "",
    settings: dict | None = None,
    commit: str | None = None,
    root: Path = ROOT,
) -> dict:
    """The manifest of a release, as a dict (its ID last, from a hash of the rest)."""
    schema = assistant.response_format()
    manifest = {
        "code": {
            "version": VERSION,
            "commit": commit if commit is not None else git_commit(root),
            "fingerprint": code_fingerprint(root),
            "image": image,
        },
        "database": {"migrations": len(migrations(root)), "last_migration": migrations(root)[-1]},
        "assistant": {
            "prompt": prompt,
            "prompt_fingerprint": assistant.fingerprint(prompt),
            "schema": schema["json_schema"]["name"],
            "schema_fingerprint": sha12(json.dumps(schema, sort_keys=True).encode()),
            "max_completion_tokens": assistant.MAX_TOKENS,
        },
        "model": {
            "deployment": assistant.CHAT_MODEL,
            "expected_version": expected_model_version,
            "embedding": ai.EMBEDDING_VERSION,
        },
        "retrieval": {
            "answer_prompt": ai.ANSWER_PROMPT,
            "search": "PostgreSQL full-text search, the 2 best documents",
            "index_version": index_version
            or "not pinned (python -m scripts.reindex --check says if the index is current)",
        },
        "data": {
            "evaluation_set": EVALUATION_SET["version"],
            "evaluation_inputs": EVALUATION_SET["inputs_version"],
            "evidence": evidence or "none",
        },
        "settings": dict(sorted((settings or {}).items())),
    }
    digest = sha12(json.dumps(manifest, sort_keys=True).encode())[:6]
    return {"id": f"{VERSION}-{digest}", **manifest}


def to_toml(manifest: dict) -> str:
    """A small TOML writer for the manifest's two levels (strings, numbers, booleans)."""

    def value(v) -> str:
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        return json.dumps(str(v), ensure_ascii=False)

    lines = [
        "# A release manifest: every version that makes this release's answers.",
        "# Written by python -m ops release build. Do not edit: a change makes a new release.",
        f"id = {value(manifest['id'])}",
    ]
    for section, items in manifest.items():
        if section == "id":
            continue
        lines += ["", f"[{section}]"]
        lines += [f"{k} = {value(v)}" for k, v in items.items()]
    return "\n".join(lines) + "\n"


def load(release_id: str, folder: Path | None = None) -> Release:
    path = Path(folder or FOLDER) / f"{release_id}.toml"
    if not path.exists():
        raise ReleaseError(f"no release manifest {path}")
    with path.open("rb") as f:
        manifest = tomllib.load(f)
    a = manifest["assistant"]
    return Release(manifest["id"], a["prompt"], a["prompt_fingerprint"], manifest)


def check(release: Release) -> list[str]:
    """What does not match between the manifest and the files that would run."""
    problems = []
    try:
        now = assistant.fingerprint(release.prompt)
    except ValueError as error:
        return [str(error)]
    if now != release.prompt_fingerprint:
        problems.append(
            f"prompt {release.prompt}: the manifest has fingerprint {release.prompt_fingerprint}, "
            f"the file now has {now}"
        )
    last = migrations()[-1]
    if last != release.manifest["database"]["last_migration"]:
        problems.append(
            f"migrations: the manifest ends with {release.manifest['database']['last_migration']}, "
            f"the project with {last}"
        )
    return problems
