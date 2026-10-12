"""The normalised representation: every path (text layer, OCR, vision) gives pages of lines with boxes.

A Line is a run of words on one row, with its box on the page. The box is in the page's own unit:
points (1/72 inch) for a PDF page read from its text layer, pixels for an image (a photo, a scan,
or a PDF page drawn as an image). With the file and the page number, the box is the line's
source: you can always go back and look at it.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field


@dataclass
class Line:
    text: str
    box: tuple[float, float, float, float]  # x0, top, x1, bottom
    score: float = 1.0  # how sure the reader was (OCR); 1.0 for the PDF text layer
    size: float = 0.0  # font size in points (text layer) or the box height
    bold: bool = False
    angle: float = 0.0  # the slope of the line in degrees (OCR on a crooked page)

    @property
    def cx(self) -> float:
        return (self.box[0] + self.box[2]) / 2

    @property
    def cy(self) -> float:
        return (self.box[1] + self.box[3]) / 2

    @property
    def height(self) -> float:
        return self.box[3] - self.box[1]


@dataclass
class Page:
    file: str
    page: int  # 1 = the first page
    width: float
    height: float
    unit: str  # "pt" or "px"
    path: str  # "text", "ocr", "vision"
    lines: list[Line] = field(default_factory=list)
    seconds: float = 0.0
    engine: str = ""
    dpi: int = 0  # a PDF page read as a picture: pixels per inch of that picture (0 = an image file)
    prepared: dict = field(default_factory=dict)  # image preparation steps (see prepare.py)

    def text(self) -> str:
        return "\n".join(" ".join(ln.text for ln in row) for row in rows(self.lines))

    def to_dict(self) -> dict:
        d = asdict(self)
        d["lines"] = [asdict(ln) | {"box": [round(v, 1) for v in ln.box]} for ln in self.lines]
        return d

    @staticmethod
    def from_dict(d: dict) -> Page:
        d = dict(d)
        d["lines"] = [Line(**(ln | {"box": tuple(ln["box"])})) for ln in d.get("lines", [])]
        return Page(**d)


def skew(lines: list[Line]) -> float:
    """The page's slope in degrees: the median slope of the longer lines (0 for a straight page,
    about 90 or 270 for a page that lies on its side)."""
    angles = sorted(ln.angle % 360 for ln in lines
                    if max(ln.box[2] - ln.box[0], ln.height) > 3 * max(min(ln.box[2] - ln.box[0], ln.height), 1))
    if not angles:
        return 0.0
    a = angles[len(angles) // 2]
    return a - 360 if a > 180 else a


def rows(lines: list[Line], tolerance: float = 0.5) -> list[list[Line]]:
    """Group lines into rows, top to bottom, each row left to right.

    Two lines are on the same row when their centres are closer than `tolerance` x the line height,
    measured along the page's slope, so a crooked photo still pairs "TOTAL" with its amount."""
    if not lines:
        return []
    a = math.radians(skew(lines))
    sideways = abs(math.sin(a)) > abs(math.cos(a))

    # Turn every centre back by the page's slope, then compare heights.
    def y(ln: Line) -> float:
        return -ln.cx * math.sin(a) + ln.cy * math.cos(a)

    def x(ln: Line) -> float:
        return ln.cx * math.cos(a) + ln.cy * math.sin(a)

    def thick(ln: Line) -> float:
        return (ln.box[2] - ln.box[0]) if sideways else ln.height

    out: list[list[Line]] = []
    for ln in sorted(lines, key=y):
        if out:
            last = out[-1]
            ref = sum(y(m) for m in last) / len(last)
            h = max(min(thick(m) for m in last), thick(ln), 1.0)
            if abs(y(ln) - ref) < tolerance * h:
                last.append(ln)
                continue
        out.append([ln])
    return [sorted(r, key=x) for r in out]


def row_text(row: list[Line]) -> str:
    return "  ".join(ln.text for ln in row)
