"""Input handling: check every file before anything reads it.

    python -m doc_extract.intake             # the course's documents, in the order they arrived
    python -m doc_extract.intake --max-mb 2  # try another size limit

The checks, in this order (the first problem stops the file):
  too_large        bigger than MAX_FILE_MB (8 MB by default)
  empty            0 bytes
  unsupported      not a PDF, JPEG, PNG, TIFF or XLSX (the first bytes decide, not the name)
  corrupt          the file cannot be opened (for example a download that stopped)
  password         a PDF that needs a password
  duplicate        the same bytes as a file that arrived before (SHA-256): not read again
  wrong_extension  the name does not match the content: accepted, read as what it really is

A near duplicate (a second scan or photo of the same receipt) has different bytes, so its hash is
different. An image fingerprint finds it, but it also finds receipts that only look alike:

    python -m doc_extract.intake --fingerprints    # the closest pairs of pages

The course decides near duplicates on the content instead, after extraction (validate.py:
the same order number, date and total).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from doc_extract.route import sniff

ACCEPTED = {"pdf", "jpeg", "png", "tiff", "xlsx"}
NEAR_DUPLICATE_BITS = 10  # fingerprints closer than this look like the same page


def max_bytes() -> int:
    return int(float(os.environ.get("MAX_FILE_MB", "8")) * 1_000_000)


@dataclass
class Intake:
    file: str
    status: str
    reason: str
    format: str = ""
    sha256: str = ""
    fingerprint: str = ""
    same_as: str = ""

    @property
    def accepted(self) -> bool:
        return self.status in ("accepted", "wrong_extension")


@dataclass
class Registry:
    """What arrived before: hashes and fingerprints. A real system keeps this in a database."""
    by_sha: dict[str, str] = field(default_factory=dict)


def fingerprint(path: Path, fmt: str) -> str:
    """A 256-bit difference hash of the first page: the page is cropped to its content, shrunk to
    17 x 16 grey pixels, and each bit says whether a pixel is brighter than its right neighbour.
    Two scans of the same receipt give almost the same bits; different receipts do not."""
    from PIL import Image

    from doc_extract import files
    from doc_extract.prepare import content_box

    img = files.page_image(path, 1, dpi=60) if fmt == "pdf" else Image.open(path).convert("RGB")
    img = img.crop(content_box(img)).convert("L").resize((17, 16), Image.LANCZOS)
    px = list(img.tobytes())
    bits = "".join("1" if px[r * 17 + c] > px[r * 17 + c + 1] else "0" for r in range(16) for c in range(16))
    return f"{int(bits, 2):064x}"


def distance(a: str, b: str) -> int:
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def _opens(path: Path, fmt: str) -> str:
    """'' if the file opens, else 'corrupt' or 'password' with the reason after a colon."""
    try:
        if fmt == "pdf":
            from pypdf import PdfReader
            from pypdf.errors import PdfReadError

            try:
                reader = PdfReader(path, strict=True)
            except PdfReadError as e:
                return f"corrupt:{e}"
            if reader.is_encrypted and not reader.decrypt(""):
                return "password:the PDF needs a password to open"
            import pypdfium2 as pdfium

            doc = pdfium.PdfDocument(path)
            try:
                doc[0].render(scale=0.1)
            finally:
                doc.close()
        elif fmt in ("jpeg", "png", "tiff"):
            from PIL import Image

            with Image.open(path) as img:
                img.load()
        elif fmt == "xlsx":
            with zipfile.ZipFile(path) as z:
                bad = z.testzip()
                if bad:
                    return f"corrupt:damaged part {bad}"
            from openpyxl import load_workbook

            load_workbook(path, read_only=True).close()
    except Exception as e:  # any reader error means: we cannot read this file as it is
        return f"corrupt:{type(e).__name__}: {str(e)[:80]}"
    return ""


def check(path: Path, registry: Registry) -> Intake:
    size = path.stat().st_size
    if size > max_bytes():
        return Intake(path.name, "too_large", f"{size / 1e6:.1f} MB is over the limit of {max_bytes() / 1e6:.1f} MB")
    if size == 0:
        return Intake(path.name, "empty", "the file has 0 bytes")
    data = path.read_bytes()
    fmt = sniff(data)
    if fmt not in ACCEPTED:
        return Intake(path.name, "unsupported", f"the content is not a PDF, image or spreadsheet ({fmt})", fmt)
    problem = _opens(path, fmt)
    if problem:
        status, reason = problem.split(":", 1)
        return Intake(path.name, status, reason.strip(), fmt)
    sha = hashlib.sha256(data).hexdigest()
    if sha in registry.by_sha:
        return Intake(path.name, "duplicate", f"the same bytes as {registry.by_sha[sha]}", fmt, sha,
                      same_as=registry.by_sha[sha])
    registry.by_sha[sha] = path.name
    from doc_extract.route import EXTENSIONS

    if path.suffix.lower() not in EXTENSIONS[fmt]:
        return Intake(path.name, "wrong_extension", f"the name ends in {path.suffix}, but the content is {fmt}", fmt, sha)
    return Intake(path.name, "accepted", "", fmt, sha)


def closest_pairs(paths: list[Path], n: int = 10) -> list[tuple[int, str, str]]:
    """The n pairs of pages whose fingerprints are closest (fewest different bits)."""
    from itertools import combinations

    prints = {}
    for p in paths:
        fmt = sniff(p.read_bytes()[:8192])
        if fmt in ("pdf", "jpeg", "png") and not _opens(p, fmt):
            prints[p.name] = fingerprint(p, fmt)
    pairs = sorted((distance(prints[a], prints[b]), a, b) for a, b in combinations(prints, 2))
    return pairs[:n]


def main(argv: list[str] | None = None) -> None:
    from doc_extract import documents

    ap = argparse.ArgumentParser(description="Check the course's documents before reading them.")
    ap.add_argument("--max-mb", type=float, help="the size limit in MB (default: MAX_FILE_MB or 8)")
    ap.add_argument("--fingerprints", action="store_true", help="print the pages that look most alike")
    args = ap.parse_args(argv)
    if args.fingerprints:
        docs = [d for d in documents.load() if d.path.stat().st_size <= max_bytes()]
        for bits, a, b in closest_pairs([d.path for d in docs], 12):
            print(f"{bits:>3} of 256 bits differ: {a} / {b}")
        return
    if args.max_mb:
        os.environ["MAX_FILE_MB"] = str(args.max_mb)
    registry = Registry()
    counts: dict[str, int] = {}
    for d in documents.load():
        r = check(d.path, registry)
        counts[r.status] = counts.get(r.status, 0) + 1
        if r.status != "accepted":
            print(f"{d.doc_id}  {d.file:<34} {r.status:<16} {r.reason}")
    print("  " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
