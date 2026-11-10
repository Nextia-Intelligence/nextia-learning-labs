"""Normalise values so that equal things look equal (Module 2, lesson 1).

Each function takes one value as text and returns its normal form. An empty string means "no value".
"""

import re
import unicodedata

TITLES = {"mr", "mrs", "ms", "miss", "dr", "m", "mme", "mlle", "prof", "sir"}
COMPANY_SUFFIXES = {"inc", "incorporated", "ltd", "limited", "ltee", "llc", "corp", "corporation", "co", "company",
                    "plc", "sa", "sarl", "gmbh", "enr", "senc"}
STREET_TYPES = {"street": "st", "st": "st", "avenue": "ave", "ave": "ave", "av": "ave", "road": "rd", "rd": "rd",
                "lane": "ln", "ln": "ln", "crescent": "cres", "cres": "cres", "drive": "dr", "dr": "dr",
                "court": "crt", "crt": "crt", "ct": "crt", "boulevard": "blvd", "blvd": "blvd", "boul": "blvd",
                "way": "way", "place": "pl", "pl": "pl", "rue": "rue", "r": "rue", "chemin": "ch", "ch": "ch",
                "rang": "rang"}
UNIT_WORDS = {"apt", "app", "apartment", "appartement", "unit", "suite"}
_PUNCT = re.compile(r"[^\w\s]")
_SPACES = re.compile(r"\s+")


def strip_accents(s):
    """é -> e, ç -> c, ñ -> n (the letter stays, the accent goes)."""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def text(s):
    """Lower case, no accents, punctuation to spaces, one space between words."""
    s = strip_accents(str(s or "")).lower()
    s = _PUNCT.sub(" ", s.replace("'", ""))
    return _SPACES.sub(" ", s).strip()


def saints(s):
    """'sainte anne' and 'ste anne' -> 'ste anne'; 'saint pierre' and 'st pierre' -> 'st pierre'."""
    s = re.sub(r"\bsainte\b", "ste", s)
    return re.sub(r"\bsaint\b", "st", s)


def name(s):
    """A person's name: text(), no titles (Mr, Dr, Mme ...), Saint and Sainte shortened."""
    words = [w for w in text(s).split() if w not in TITLES]
    return saints(" ".join(words))


def company(s):
    """A company name: text() without legal suffixes (Inc, Ltd, Ltée ...)."""
    words = text(s).split()
    while words and words[-1] in COMPANY_SUFFIXES:
        words.pop()
    return " ".join(words)


def phone(s):
    """Ten digits for a North American number ('(514) 555-0123' -> '5145550123'); '' when it is not one."""
    s = re.split(r"(?i)\s*(ext|x|poste)\.?\s*\d+$", str(s or ""))[0]
    d = re.sub(r"\D", "", s)
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]
    return d if len(d) == 10 else ""


def email(s):
    """No spaces around, lower case. ('  Marie.Roy@Example.com ' -> 'marie.roy@example.com')."""
    e = str(s or "").strip().lower()
    return e if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e) else ""


def postcode(s):
    """A Canadian postcode as six characters without a space ('j0l-1a0' -> 'J0L1A0'); '' when it is not one."""
    p = re.sub(r"[\s-]", "", str(s or "")).upper()
    return p if re.fullmatch(r"[A-Z]\d[A-Z]\d[A-Z]\d", p) else ""


def street(s):
    """A street: text(), street types in one short form (Street, St., St -> st; rue, r. -> rue), no unit words."""
    words = []
    for w in text(s).split():
        if w in UNIT_WORDS:
            continue
        words.append(STREET_TYPES.get(w, w))
    return saints(" ".join(words))


def town(s):
    return saints(text(s))


def date(s):
    """A date as YYYY-MM-DD from 'YYYY-MM-DD' or 'DD/MM/YYYY'; '' when it is neither."""
    s = str(s or "").strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return ""
