"""Cut a parsed document into chunks: one chunk per section (the RAG course's structure chunker, MIT).

A section runs from its heading to the next heading. A section longer than MAX_WORDS is split
between blocks, never inside a table. Each chunk starts with the document title (and the section
heading when a part does not start with it), so that a chunk keeps its context.

A chunk ID is the first 12 hexadecimal characters of SHA-256 over
"tenant|doc_key|version|start|end": the same chunk gets the same ID every time it is indexed (a
citation stays valid), a new version gets new IDs, and two shops never share an ID even when
they upload the same file.
"""

import hashlib
from dataclasses import dataclass

from .parse import ParsedDocument

MAX_WORDS = 200


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    position: int
    section: str
    text: str          # the text that is indexed and shown to the model
    start: int         # character positions in ParsedDocument.text
    end: int
    pages: tuple       # PDF pages; empty for Markdown and HTML


def chunk_id(tenant: str, doc_key: str, version: str, start: int, end: int) -> str:
    return hashlib.sha256(f"{tenant}|{doc_key}|{version}|{start}|{end}".encode()).hexdigest()[:12]


def structure(doc: ParsedDocument, tenant: str, doc_key: str, version: str, title: str,
              max_words: int = MAX_WORDS) -> list[Chunk]:
    sections: list[list] = []
    for b in doc.blocks:
        if b.kind == "heading" or not sections:
            sections.append([])
        if b.kind != "title":
            sections[-1].append(b)
    chunks: list[Chunk] = []

    def add(blocks: list, heading: str) -> None:
        start, end = blocks[0].start, blocks[-1].end
        prefix = title if blocks[0].kind == "heading" or not heading else f"{title}\n{heading}"
        pages = tuple(sorted({b.page for b in blocks if b.page is not None}))
        chunks.append(Chunk(chunk_id(tenant, doc_key, version, start, end), len(chunks), heading,
                            f"{prefix}\n{doc.text[start:end]}", start, end, pages))

    for blocks in sections:
        if not blocks:
            continue
        heading = blocks[0].text if blocks[0].kind == "heading" else ""
        part: list = []
        for b in blocks:
            words = sum(len(x.text.split()) for x in part)
            if part and words + len(b.text.split()) > max_words:
                add(part, heading)
                part = []
            part.append(b)
        add(part, heading)
    return chunks
