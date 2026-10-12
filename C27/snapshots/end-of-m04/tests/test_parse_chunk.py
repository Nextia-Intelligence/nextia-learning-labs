"""Parsing the three formats and cutting chunks (the RAG course's parser and chunker)."""

from pathlib import Path

import pytest

from doc_assistant.chunk import chunk_id, structure
from doc_assistant.parse import ParseError, parse

DATA = Path(__file__).resolve().parent.parent / "data"


def read(tenant: str, name: str) -> bytes:
    return (DATA / tenant / "documents" / name).read_bytes()


def test_markdown_front_matter_and_sections():
    doc = parse("gift-cards.md", read("bramble", "gift-cards.md"))
    assert doc.meta["doc_id"] == "gift-cards" and doc.meta["access"] == "public"
    assert [b.text for b in doc.blocks if b.kind == "heading"] == ["Amounts", "Where to use them",
                                                                   "How long they last", "Refunds"]


def test_html_keeps_only_the_article():
    doc = parse("returns-policy.v2.html", read("bramble", "returns-policy.v2.html"))
    assert doc.meta["version"] == "2" and doc.meta["effective_from"] == "2026-12-01"
    assert "cookies" not in doc.text and "Related" not in doc.text and "Version 2. In force" not in doc.text
    assert "Holiday gifts" in doc.text


def test_pdf_table_rows_are_rebuilt():
    doc = parse("events-and-room-hire.pdf", read("bramble", "events-and-room-hire.pdf"))
    tables = [b.text for b in doc.blocks if b.kind == "table"]
    assert tables == ["Booking | When | Price\nWeekday evening | Wednesday to Friday, 6 pm to 9 pm | 45 dollars\n"
                      "Saturday afternoon | 1 pm to 5 pm | 70 dollars\nCommunity groups | Tuesday, 6 pm to 9 pm | Free"]
    assert "Page 1 of 1" not in doc.text   # the footer in the margin is dropped


@pytest.mark.parametrize("name, data, message", [
    ("broken.pdf", b"%PDF-1.4\nthis is not really a PDF", "not a readable PDF"),
    ("photo.pdf", b"\x89PNG\r\n\x1a\n", "not a PDF"),
    ("notes.docx", b"PK\x03\x04", "Cannot read .docx"),
    ("empty.md", b"---\ntitle: x\n---\n", "No text"),
    ("latin.md", "caf\xe9".encode("latin-1"), "not UTF-8"),
])
def test_files_that_cannot_be_read(name, data, message):
    with pytest.raises(ParseError, match=message):
        parse(name, data)


def test_chunks_start_with_the_title_and_have_stable_ids():
    doc = parse("gift-cards.md", read("bramble", "gift-cards.md"))
    chunks = structure(doc, "bramble", "gift-cards", "1", "Gift cards")
    assert len(chunks) == 4
    assert chunks[2].text.startswith("Gift cards\nHow long they last\n")
    assert chunks[2].chunk_id == chunk_id("bramble", "gift-cards", "1", chunks[2].start, chunks[2].end)
    doc2 = parse("gift-cards.md", read("bramble", "gift-cards.md"))
    again = structure(doc2, "bramble", "gift-cards", "1", "Gift cards")
    assert [c.chunk_id for c in again] == [c.chunk_id for c in chunks]


def test_the_same_file_in_two_shops_gets_different_ids():
    doc = parse("gift-cards.md", read("bramble", "gift-cards.md"))
    a = structure(doc, "bramble", "gift-cards", "1", "Gift cards")
    b = structure(doc, "larkfield", "gift-cards", "1", "Gift cards")
    assert not {c.chunk_id for c in a} & {c.chunk_id for c in b}
