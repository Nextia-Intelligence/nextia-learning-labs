"""Rebuild the answers' retrieval index from the current documents (the MLOps course, Module 4).

    python -m scripts.reindex            rebuild it
    python -m scripts.reindex --check    only say if it is up to date

The index is a copy of the documents. When a document changes, the index must be rebuilt, or
the answers keep quoting the old version.
"""

import argparse
import sys

import psycopg
from psycopg.rows import dict_row

from ticket_api import repository
from ticket_api.config import load_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="do not rebuild; compare only")
    args = parser.parse_args(argv)
    with psycopg.connect(load_settings().database_url, row_factory=dict_row) as conn:
        docs, index = repository.documents_version(conn), repository.index_version(conn)
        if args.check:
            state = "up to date" if docs == index else "OLDER than the documents"
            print(f"Index version {index}, documents version {docs}: the index is {state}.")
            return 0 if docs == index else 1
        version, n = repository.rebuild_answer_index(conn)
    print(f"Rebuilt the index from {n} current documents: index version {version} (was {index}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
