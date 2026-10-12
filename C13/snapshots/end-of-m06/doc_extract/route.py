"""Look inside each file and choose how to read it (the route), page by page.

    python -m doc_extract.route            # every document of the course's set
    python -m doc_extract.route D058       # one document, page by page

The route of a page:
  text   the PDF page has a text layer: read it directly (textlayer.py)
  ocr    the page is only a picture (a scan, a photo, a scanned PDF page): read it with OCR (ocr.py)
  sheet  a spreadsheet: read the cells (sheets.py)
  stop   the file cannot be read as it is (see intake.py)
"""

from __future__ import annotations

import io
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

MIN_TEXT_CHARS = 30  # fewer characters than this on a page: treat the page as a picture


def sniff(data: bytes) -> str:
    """The real format, from the first bytes of the file (its "magic number"), not from its name."""
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if data[:4] == b"PK\x03\x04":
        try:
            names = zipfile.ZipFile(io.BytesIO(data)).namelist()
        except zipfile.BadZipFile:
            return "zip"
        return "xlsx" if any(n.startswith("xl/") for n in names) else "zip"
    return "unknown"


EXTENSIONS = {"pdf": {".pdf"}, "jpeg": {".jpg", ".jpeg"}, "png": {".png"}, "tiff": {".tif", ".tiff"},
              "xlsx": {".xlsx"}}


@dataclass
class PageInfo:
    page: int
    chars: int  # characters in the text layer
    image_share: float  # share of the page covered by pictures (0 to 1)
    route: str
    why: str


@dataclass
class Inspection:
    file: str
    format: str
    extension_ok: bool
    pages: list[PageInfo] = field(default_factory=list)
    note: str = ""

    @property
    def routes(self) -> list[str]:
        return [p.route for p in self.pages]

    @property
    def kind(self) -> str:
        """digital, scan, photo, spreadsheet, mixed or unreadable: what a person would call the file."""
        r = set(self.routes)
        if not r or r == {"stop"}:
            return "unreadable"
        if r == {"sheet"}:
            return "spreadsheet"
        if r == {"text"}:
            return "digital"
        if r == {"text", "ocr"}:
            return "mixed"
        return "photo" if "photo" in self.note else "scan"


def _looks_like_photo(path: Path) -> bool:
    """A photo has a coloured background around the paper; a scan is grey on white."""
    from PIL import Image

    with Image.open(path) as img:
        small = img.convert("RGB").resize((64, 64))
    border = [small.getpixel((x, y)) for x in range(64) for y in (0, 63)] + \
             [small.getpixel((x, y)) for y in range(64) for x in (0, 63)]
    sat = sum(max(p) - min(p) for p in border) / len(border)
    bright = sum(sum(p) / 3 for p in border) / len(border)
    return sat > 18 or bright < 170


def inspect(path: Path) -> Inspection:
    data = path.read_bytes()
    fmt = sniff(data)
    ok = path.suffix.lower() in EXTENSIONS[fmt] if fmt in EXTENSIONS else True
    out = Inspection(path.name, fmt, ok)
    if fmt == "pdf":
        import pdfplumber

        try:
            with pdfplumber.open(path) as pdf:
                for i, p in enumerate(pdf.pages, 1):
                    chars = len(p.chars)
                    area = float(p.width * p.height) or 1.0
                    covered = sum(max(0.0, (im["x1"] - im["x0"]) * (im["bottom"] - im["top"])) for im in p.images)
                    share = min(1.0, covered / area)
                    if chars >= MIN_TEXT_CHARS:
                        out.pages.append(PageInfo(i, chars, round(share, 2), "text", f"{chars} characters in the text layer"))
                    elif share > 0.5:
                        out.pages.append(PageInfo(i, chars, round(share, 2), "ocr", "a picture covers the page, no text layer"))
                    else:
                        out.pages.append(PageInfo(i, chars, round(share, 2), "ocr", "almost no text and no large picture"))
        except Exception as e:  # encrypted, broken: intake.py says which
            out.pages.append(PageInfo(1, 0, 0.0, "stop", f"cannot open: {type(e).__name__}"))
    elif fmt in ("jpeg", "png", "tiff"):
        photo = _looks_like_photo(path)
        out.note = "photo" if photo else "scan"
        out.pages.append(PageInfo(1, 0, 1.0, "ocr", "a phone photo (background around the paper)" if photo
                                  else "a scanned image (white page)"))
    elif fmt == "xlsx":
        out.pages.append(PageInfo(1, 0, 0.0, "sheet", "a spreadsheet: read the cells, not a picture of them"))
    else:
        out.pages.append(PageInfo(1, 0, 0.0, "stop", f"not a supported format ({fmt})"))
    return out


def main(argv: list[str] | None = None) -> None:
    from doc_extract import documents

    argv = sys.argv[1:] if argv is None else argv
    if argv:
        d = documents.get(argv[0])
        i = inspect(d.path)
        name_note = "" if i.extension_ok else f"  <- the name says {Path(d.file).suffix}"
        print(f"{d.doc_id}  {d.file}: format {i.format}{name_note}, {len(i.pages)} page(s), kind {i.kind}")
        for p in i.pages:
            print(f"  page {p.page}: route {p.route:<5} ({p.why}; pictures cover {p.image_share:.0%})")
        return
    counts: dict[str, int] = {}
    print(f"{'ID':<5} {'file':<34} {'format':<7} {'kind':<11} routes")
    for d in documents.load():
        i = inspect(d.path)
        counts[i.kind] = counts.get(i.kind, 0) + 1
        flag = "" if i.extension_ok else "  (wrong extension)"
        print(f"{d.doc_id:<5} {d.file[:34]:<34} {i.format:<7} {i.kind:<11} {' '.join(i.routes)}{flag}")
    print("  " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
