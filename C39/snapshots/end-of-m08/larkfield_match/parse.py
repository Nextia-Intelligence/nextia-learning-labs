"""Split values into parts (Module 2, lesson 2): names, addresses and product titles.

Every parser returns a dict with `ok`: False when the value did not have the expected shape. A record that does
not parse keeps its raw value; matching then uses the fields it has.
"""

import re

from . import normalise as nz

PROVINCES = {"QC", "ON", "NB", "BC", "AB", "MB", "NS", "PE", "NL", "SK", "YT", "NT", "NU"}
_POSTCODE_END = re.compile(r"\s*([A-Za-z]\d[A-Za-z])[\s-]?(\d[A-Za-z]\d)\s*$")
_UNIT_FIRST = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*,?\s+")
_UNIT_WORD = re.compile(r"[,\s]*(?:apt|app|apartment|unit|suite|#)\.?\s*(\d+)\b", re.IGNORECASE)
_NUMBER = re.compile(r"^\s*(\d+)\s*,?\s+")


def split_name(raw):
    """'TREMBLAY, MARIE-CLAUDE' and 'Dr. Marie-Claude Tremblay' -> first 'marie claude', last 'tremblay'.

    With a comma, the part before it is the surname. Without one, the last word is the surname.
    """
    raw = str(raw or "").strip()
    if not raw:
        return {"first": "", "last": "", "ok": False}
    if "," in raw:
        last, first = raw.split(",", 1)
        first, last = nz.name(first), nz.name(last)
    else:
        words = [w for w in raw.split() if nz.text(w) not in nz.TITLES]
        if len(words) < 2:
            return {"first": "", "last": nz.name(raw), "ok": False}
        first, last = nz.name(" ".join(words[:-1])), nz.name(words[-1])
    return {"first": first, "last": last, "ok": bool(first and last)}


def split_address(raw):
    """'6760, r. des Hérons, Saint-Éloi-du-Lac QC H6O 3H7' -> number, street, unit, town, province, postcode."""
    s = str(raw or "").strip()
    out = {"number": "", "street": "", "unit": "", "town": "", "province": "", "postcode": "", "ok": False}
    if not s:
        return out
    m = _POSTCODE_END.search(s)
    if m:
        out["postcode"] = (m.group(1) + m.group(2)).upper()
        s = s[:m.start()]
    words = s.rstrip(", ").split()
    if words and words[-1].upper() in PROVINCES:
        out["province"] = words[-1].upper()
        s = " ".join(words[:-1])
    if "," in s:
        s, town = s.rsplit(",", 1)
        out["town"] = nz.town(town)
    m = _UNIT_FIRST.match(s)
    if m:
        out["unit"], s = m.group(1), m.group(2) + " " + s[m.end():]
    m = _UNIT_WORD.search(s)
    if m:
        out["unit"], s = m.group(1), s[:m.start()] + s[m.end():]
    m = _NUMBER.match(s)
    if m:
        out["number"], s = m.group(1), s[m.end():]
    out["street"] = nz.street(s)
    out["ok"] = bool(out["number"] and out["street"] and out["town"])
    return out


# Product titles: sizes in many units, and packs.
_PACK = re.compile(r"\(pack of (\d+)\)|pack of (\d+)|(\d+)\s*-\s*pack|\bx\s?(\d+)\b|(\d+)\s*pk\b|\((\d+)\)", re.IGNORECASE)
_SIZE = re.compile(r"(\d+(?:\.\d+)?)\s*(sq ft|m2|ft|cm|in|m|l|kg|lb|w|lm)\b", re.IGNORECASE)
TO_BASE = {"ft": ("length_m", 0.3048), "m": ("length_m", 1.0), "cm": ("length_m", 0.01), "in": ("length_m", 0.0254),
           "kg": ("weight_kg", 1.0), "lb": ("weight_kg", 0.453592), "l": ("volume_l", 1.0), "w": ("watts", 1.0),
           "lm": ("lumens", 1.0), "sq ft": ("area_m2", 0.092903), "m2": ("area_m2", 1.0)}
PRODUCT_WORDS = {"gdn": "garden", "sol": "solar", "pot": "potting", "color": "colour", "gray": "grey",
                 "fertilizer": "fertiliser", "galvanized": "galvanised", "aluminum": "aluminium",
                 "fiberglass": "fibreglass"}


def parse_title(raw):
    """'AquaRidge Rubber Garden Hose, 50 ft, Green (Pack of 2)' -> size 15.24 length_m, pack 2, words."""
    s = str(raw or "")
    pack = 1
    m = _PACK.search(s)
    if m:
        pack = int(next(g for g in m.groups() if g))
        s = s[:m.start()] + " " + s[m.end():]
    size, kind = None, ""
    m = _SIZE.search(s)
    if m:
        kind, factor = TO_BASE[m.group(2).lower()]
        size = round(float(m.group(1)) * factor, 2)
        s = s[:m.start()] + " " + s[m.end():]
    words = [PRODUCT_WORDS.get(w, w) for w in nz.text(s).split()]
    return {"size": size, "size_kind": kind, "pack": pack, "words": " ".join(words), "ok": size is not None}
