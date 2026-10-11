"""Publish a new version of a shop document (the MLOps course, Module 4).

    python -m scripts.update_document delivery-policy --replace "free at 100" "free at 75"

Grace's team changes a document: the old version ends today, the new version (version + 1)
starts today. Nothing else happens: the answers' retrieval index still has the old text until
someone runs python -m scripts.reindex. That is the stale index of Lesson 3 (a practice change
that we make on purpose).
"""

import argparse
import hashlib
import sys

import psycopg
from psycopg.rows import dict_row

from ticket_api.config import load_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("doc_id")
    parser.add_argument("--replace", nargs=2, metavar=("OLD", "NEW"), required=True)
    args = parser.parse_args(argv)
    old_text, new_text = args.replace
    with psycopg.connect(load_settings().database_url, row_factory=dict_row) as conn:
        doc = conn.execute(
            "SELECT * FROM documents WHERE doc_id = %s AND effective_to IS NULL", (args.doc_id,)
        ).fetchone()
        if doc is None:
            print(f"No current document {args.doc_id}.", file=sys.stderr)
            return 1
        if old_text not in doc["body"]:
            print(
                f"Version {doc['version']} of {args.doc_id} has no text {old_text!r}.",
                file=sys.stderr,
            )
            return 1
        body = doc["body"].replace(old_text, new_text)
        conn.execute(
            "UPDATE documents SET effective_to = current_date WHERE doc_id = %s AND version = %s",
            (args.doc_id, doc["version"]),
        )
        conn.execute(
            "INSERT INTO documents (doc_id, version, title, doc_type, language, access,"
            " effective_from, body, sha256) VALUES (%s, %s, %s, %s, %s, %s, current_date, %s, %s)",
            (
                args.doc_id,
                doc["version"] + 1,
                doc["title"],
                doc["doc_type"],
                doc["language"],
                doc["access"],
                body,
                hashlib.sha256(body.encode()).hexdigest(),
            ),
        )
    print(
        f"{args.doc_id}: version {doc['version'] + 1} is current (was {doc['version']}). "
        "The answers' index still has the old text: python -m scripts.reindex --check"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
