"""The course's document set: list the documents and their true values.

    python -m doc_extract.documents           # one line per document
    python -m doc_extract.documents D007      # everything about one document, with its true values
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    return Path(os.environ.get("DOCS_DIR", ROOT / "data"))


@dataclass
class Document:
    doc_id: str
    file: str
    kind: str
    source: str
    language: str
    pages: int
    bytes: int
    sha256: str
    expected_intake: str
    conditions: dict
    truth: dict

    @property
    def path(self) -> Path:
        return data_dir() / "documents" / self.file

    @property
    def fields(self) -> dict:
        return self.truth.get("fields", {})


def load(folder: Path | None = None) -> list[Document]:
    folder = folder or data_dir()
    p = folder / "truth.jsonl"
    if not p.exists():
        raise SystemExit(f"{p} does not exist. Make the documents first: python -m doc_extract.generate")
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            out.append(Document(**d))
    return out


def get(doc_id: str) -> Document:
    for d in load():
        if d.doc_id == doc_id.upper() or d.file == doc_id:
            return d
    raise SystemExit(f"No document {doc_id}. List them: python -m doc_extract.documents")


def receipts(docs: list[Document] | None = None) -> list[Document]:
    """The documents with receipt fields: receipts and the claim (its page 2 is a receipt)."""
    return [d for d in (docs or load()) if d.kind in ("receipt", "claim")]


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        d = get(argv[0])
        print(f"{d.doc_id}  {d.file}")
        print(f"  kind {d.kind}, source {d.source}, language {d.language}, pages {d.pages}, {d.bytes:,} bytes")
        if d.conditions:
            print(f"  how it was made: {json.dumps(d.conditions, ensure_ascii=False)}")
        for k, v in d.fields.items():
            print(f"  {k:<15} {v if v is not None else '(not on the document)'}")
        for item in d.truth.get("items", []):
            print(f"    item: {item['quantity']} x {item['description']} @ {item['unit_price']} = {item['line_total']}")
        return
    docs = load()
    print(f"{'ID':<5} {'file':<34} {'kind':<11} {'source':<11} {'lang':<4} pages")
    for d in docs:
        print(f"{d.doc_id:<5} {d.file[:34]:<34} {d.kind:<11} {d.source:<11} {d.language:<4} {d.pages}")
    print(f"{len(docs)} documents in {data_dir() / 'documents'}")


if __name__ == "__main__":
    main()
