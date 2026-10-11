"""Look at a document: what is in the file, and a picture of each page in out/show/.

    python -m doc_extract.show D007
"""

from __future__ import annotations

import sys
from pathlib import Path

from doc_extract import documents, files

OUT = Path("out/show")


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("usage: python -m doc_extract.show DOC_ID")
    d = documents.get(argv[0])
    print(f"{d.doc_id}  {d.file}  ({d.bytes:,} bytes, {d.source})")
    if d.path.suffix.lower() not in {".pdf", *files.IMAGE_SUFFIXES}:
        print("  not a PDF or an image: nothing to draw")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        n = files.page_count(d.path)
    except Exception as e:  # a broken or locked file: say so, do not crash
        print(f"  cannot open it: {type(e).__name__}: {e}")
        return
    for p in range(1, n + 1):
        img = files.page_image(d.path, p, dpi=100)
        out = OUT / f"{d.doc_id}-p{p}.png"
        img.save(out)
        print(f"  page {p}: {img.width} x {img.height} pixels at 100 dpi -> {out}")


if __name__ == "__main__":
    main()
