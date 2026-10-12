"""Apply the database migrations in migrations/, in order, once each.

    python -m doc_assistant.migrate            apply every migration that is not applied yet
    python -m doc_assistant.migrate --status   list the migrations and whether they are applied

Each migration runs in its own transaction, and its name and SHA-256 are recorded in
schema_migrations. A migration that was applied must never change: write a new one. If an
applied file changed, nothing runs and the command names the file. (The databases course's rules.)
"""

import argparse
import hashlib
import sys
from pathlib import Path

import psycopg

from .config import settings

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def status(conn: psycopg.Connection) -> list[tuple[str, str]]:
    conn.execute("SET client_min_messages = warning")
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, checksum text NOT NULL,"
                 " applied_at timestamptz NOT NULL DEFAULT now())")
    applied = dict(conn.execute("SELECT version, checksum FROM schema_migrations").fetchall())
    out = []
    for f in sorted(MIGRATIONS.glob("*.sql")):
        if f.stem not in applied:
            out.append((f.stem, "pending"))
        elif applied[f.stem] != checksum(f):
            out.append((f.stem, "CHANGED after it was applied"))
        else:
            out.append((f.stem, "applied"))
    return out


def migrate(url: str, quiet: bool = False) -> list[str]:
    """Apply the pending migrations. Returns their names."""
    done = []
    with psycopg.connect(url, autocommit=True) as conn:
        rows = status(conn)
        changed = [name for name, state in rows if state.startswith("CHANGED")]
        if changed:
            raise SystemExit(f"Stopped: {', '.join(changed)} changed after it was applied. Write a new migration.")
        for name, state in rows:
            if state != "pending":
                continue
            with conn.transaction():
                conn.execute((MIGRATIONS / f"{name}.sql").read_text(encoding="utf-8"))
                conn.execute("INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                             (name, checksum(MIGRATIONS / f"{name}.sql")))
            done.append(name)
            if not quiet:
                print(f"applied {name}")
    return done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m doc_assistant.migrate")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args(argv)
    url = settings().database_url
    if not url:
        print("Set DATABASE_URL (see .env.example).", file=sys.stderr)
        return 2
    if args.status:
        with psycopg.connect(url, autocommit=True) as conn:
            for name, state in status(conn):
                print(f"{name:<32} {state}")
        return 0
    done = migrate(url)
    print(f"{len(done)} migration(s) applied." if done else "The database is up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
