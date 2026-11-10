"""Measure transcripts the same way every time: normalise, align, count errors, build the comparison table.

The same file is `compare.py` in the labs folder of the Speech AI course and `larkspeech/compare.py` in the
project. It needs only the Python standard library.

    from compare import normalise, align, wer, cer, important_errors, Table

The normalisation guide (written once, used for every method; see NORMALISATION_GUIDE below):
    level "none":  split on spaces, nothing else.
    level "basic": lower case, punctuation removed.
    level "full":  basic + the rules of the guide (numbers, fillers, contractions, French elisions, ordinals).
"""
from __future__ import annotations

import json
import re
import unicodedata

NORMALISATION_GUIDE = """\
Larkfield normalisation guide (applied to the reference and to the model transcript, before any score)
1. Lower case. Curly quotes become straight quotes.
2. Punctuation is removed. A hyphen between two words becomes a space ("seventy-four" -> "seventy four").
3. Fillers are removed: um, uh, er, erm, hmm, mm, ah (English); euh, heu, ben, bah, hum (French).
4. English contractions are written out: "it's" -> "it is", "don't" -> "do not", "i'm" -> "i am" ...
5. French elisions are split: "l'article" -> "l article", "qu'elle" -> "qu elle", "c'est" -> "c est".
6. Number words become digits: "seven" -> "7", "seventy four" -> "74", "sept" -> "7", "quatorze" -> "14".
   "oh" becomes 0 only next to a digit ("seven oh two" -> "702", "one five oh" -> "150").
7. Ordinals become numbers: "fourteenth" and "14th" -> "14"; French "premier" after "le" -> "1".
8. Digits that follow each other are joined: "7 4 2 1 5 8" and "742 158" -> "742158".
   (Order numbers and card numbers are said in pieces; the transcript must not be punished for the spaces.)
9. Spaces are collapsed. Accents are kept (French "é" is not "e").
"""

FILLERS = {"um", "uh", "er", "erm", "hmm", "mm", "ah", "euh", "heu", "ben", "bah", "hum"}
CONTRACTIONS = {
    "it's": "it is", "that's": "that is", "what's": "what is", "there's": "there is", "here's": "here is",
    "he's": "he is", "she's": "she is", "let's": "let us", "i'm": "i am", "you're": "you are",
    "we're": "we are", "they're": "they are", "i've": "i have", "you've": "you have", "we've": "we have",
    "i'll": "i will", "you'll": "you will", "we'll": "we will", "it'll": "it will", "i'd": "i would",
    "you'd": "you would", "don't": "do not", "doesn't": "does not", "didn't": "did not", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not", "hasn't": "has not", "haven't": "have not",
    "hadn't": "had not", "can't": "cannot", "couldn't": "could not", "won't": "will not",
    "wouldn't": "would not", "shouldn't": "should not",
}
FR_ELISIONS = ("l'", "d'", "j'", "qu'", "n'", "c'", "s'", "m'", "t'", "jusqu'", "lorsqu'", "puisqu'")

EN_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
            "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
EN_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
           "ninety": 90}
EN_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7,
               "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12, "thirteenth": 13,
               "fourteenth": 14, "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18,
               "nineteenth": 19, "twentieth": 20, "thirtieth": 30}
FR_UNITS = {"zéro": 0, "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
            "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "treize": 13, "quatorze": 14, "quinze": 15,
            "seize": 16}
FR_TENS = {"vingt": 20, "trente": 30, "quarante": 40, "cinquante": 50, "soixante": 60}


def _basic(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text).lower().replace("’", "'").replace("‘", "'")
    text = re.sub(r"(?<=\w)-(?=\w)", " ", text)
    text = re.sub(r"[^\w\s']", " ", text)
    text = re.sub(r"(^|\s)'|'(\s|$)", " ", text)
    return text.split()


def _numbers_en(tokens: list[str]) -> list[str]:
    out, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in EN_TENS:
            v = EN_TENS[t]
            nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
            if nxt in EN_UNITS[1:10]:
                v += EN_UNITS.index(nxt)
                i += 1
            elif EN_ORDINALS.get(nxt, 99) < 10:  # twenty first -> 21 (an ordinal)
                out.append("#" + str(v + EN_ORDINALS[nxt]))
                i += 2
                continue
            out.append(str(v))
        elif t in EN_UNITS:
            out.append(str(EN_UNITS.index(t)))
        elif t in EN_ORDINALS:  # "#": an ordinal is never joined to the digits around it
            out.append("#" + str(EN_ORDINALS[t]))
        elif t.endswith("ieth") and t[:-4] + "y" in EN_TENS:
            out.append("#" + str(EN_TENS[t[:-4] + "y"]))
        elif re.fullmatch(r"\d+(st|nd|rd|th)", t):
            out.append("#" + re.sub(r"\D", "", t))
        else:
            out.append(t)
        i += 1
    return out


def _numbers_fr(tokens: list[str]) -> list[str]:
    out, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
        nxt2 = tokens[i + 2] if i + 2 < len(tokens) else ""
        if t == "quatre" and nxt in ("vingt", "vingts"):
            v, i = 80, i + 1
            nxt3 = tokens[i + 2] if i + 2 < len(tokens) else ""
            if nxt2 == "dix" and nxt3 in ("sept", "huit", "neuf"):
                v, i = 90 + FR_UNITS[nxt3], i + 2
            elif nxt2 in FR_UNITS and FR_UNITS[nxt2] < 20:
                v, i = 80 + FR_UNITS[nxt2], i + 1
            out.append(str(v))
        elif t in FR_TENS:
            v = FR_TENS[t]
            if nxt == "et" and nxt2 in ("un", "une", "onze"):
                v, i = v + FR_UNITS[nxt2], i + 2
            elif nxt in FR_UNITS and (FR_UNITS[nxt] < 10 or (t == "soixante" and FR_UNITS[nxt] < 20)):
                v, i = v + FR_UNITS[nxt], i + 1
            elif t == "soixante" and nxt == "dix":
                v, i = 70, i + 1
                if nxt2 in ("sept", "huit", "neuf"):
                    v, i = 70 + FR_UNITS[nxt2], i + 1
            out.append(str(v))
        elif t == "dix" and nxt in ("sept", "huit", "neuf"):
            out.append(str(10 + FR_UNITS[nxt]))
            i += 1
        elif t in FR_UNITS and t not in ("un", "une"):
            out.append(str(FR_UNITS[t]))
        elif t in ("un", "une") and (_isdig(out[-1:]) or _isdig([nxt]) or nxt in FR_UNITS or nxt in FR_TENS):
            out.append("1")
        elif t == "premier" and out[-1:] == ["le"]:
            out.append("#1")
        else:
            out.append(t)
        i += 1
    return out


def _isdig(xs):
    return bool(xs) and xs[0].isdigit()


def normalise(text: str, level: str = "full", language: str = "en") -> str:
    """The transcript after the normalisation guide (level none, basic or full)."""
    if level == "none":
        return " ".join(text.split())
    tokens = _basic(text)
    if level == "basic":
        return " ".join(tokens)
    tokens = [t for t in tokens if t not in FILLERS]
    expanded = []
    for t in tokens:
        if t in CONTRACTIONS:
            expanded.extend(CONTRACTIONS[t].split())
            continue
        for el in FR_ELISIONS:
            if t.startswith(el) and len(t) > len(el):
                expanded.extend([el[:-1], t[len(el):]])
                break
        else:
            expanded.append(t.replace("'", " ").strip() if "'" in t else t)
    tokens = " ".join(expanded).split()
    tokens = _numbers_fr(tokens) if language == "fr" else _numbers_en(tokens)
    tokens = _numbers_en(tokens) if language == "fr" else tokens  # French callers say English numbers sometimes
    # "oh" between digits is zero
    for i, t in enumerate(tokens):
        if t == "oh" and ((i > 0 and tokens[i - 1].isdigit()) or (i + 1 < len(tokens) and tokens[i + 1].isdigit())):
            tokens[i] = "0"
    joined = []
    for t in tokens:
        if t.isdigit() and joined and joined[-1].isdigit():
            joined[-1] += t
        else:
            joined.append(t)
    return " ".join(t.lstrip("#") for t in joined)


# ---------------------------------------------------------------- alignment and error rates

def align(ref: list[str], hyp: list[str]) -> list[tuple[str, str | None, str | None]]:
    """Minimum-edit alignment: a list of (op, ref_word, hyp_word); op is ok, sub, del or ins."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            c = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j - 1] + c, d[i - 1][j] + 1, d[i][j - 1] + 1)
    ops, i, j = [], n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + (0 if ref[i - 1] == hyp[j - 1] else 1):
            ops.append(("ok" if ref[i - 1] == hyp[j - 1] else "sub", ref[i - 1], hyp[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and d[i][j] == d[i - 1][j] + 1:
            ops.append(("del", ref[i - 1], None))
            i -= 1
        else:
            ops.append(("ins", None, hyp[j - 1]))
            j -= 1
    return ops[::-1]


def counts(ref: str, hyp: str) -> dict:
    ops = align(ref.split(), hyp.split())
    c = {"ref_words": len(ref.split()), "sub": 0, "del": 0, "ins": 0, "ok": 0}
    for op, _, _ in ops:
        c[op] += 1
    return c


def wer(ref: str, hyp: str) -> float:
    c = counts(ref, hyp)
    return (c["sub"] + c["del"] + c["ins"]) / max(c["ref_words"], 1)


def distance(ref, hyp) -> int:
    """The edit distance (substitutions + deletions + insertions) without the alignment: faster, for CER."""
    prev = list(range(len(hyp) + 1))
    for i, a in enumerate(ref, 1):
        cur = [i]
        for j, b in enumerate(hyp, 1):
            cur.append(min(prev[j - 1] + (a != b), prev[j] + 1, cur[j - 1] + 1))
        prev = cur
    return prev[-1]


def cer(ref: str, hyp: str) -> float:
    return distance(ref, hyp) / max(len(ref), 1)


def corpus_scores(pairs, level="full") -> dict:
    """WER and CER over many (ref, hyp, language) items: errors summed, then divided (not a mean of rates)."""
    e = n = ce = cn = 0
    s = d = ins = 0
    for ref, hyp, lang in pairs:
        r, h = normalise(ref, level, lang), normalise(hyp, level, lang)
        c = counts(r, h)
        e += c["sub"] + c["del"] + c["ins"]
        s, d, ins = s + c["sub"], d + c["del"], ins + c["ins"]
        n += c["ref_words"]
        ce += distance(r, h)
        cn += len(r)
    return {"wer": e / max(n, 1), "cer": ce / max(cn, 1), "words": n, "sub": s, "del": d, "ins": ins}


# ---------------------------------------------------------------- the errors that matter

NEGATION = {"en": ("not", "no", "don't", "cannot"), "fr": ("ne", "n", "pas", "non")}


def important_errors(important: dict, hyp: str, language: str) -> dict:
    """For each kind of important item (order, product, date, negation, card): how many are missing from the
    normalised model transcript. An item counts as right only if all its words appear in order."""
    h = " " + normalise(hyp, "full", language) + " "
    out = {}
    for kind, items in important.items():
        miss = 0
        for item in items:
            if kind == "negation":
                words = [w for w in normalise(item, "full", language).split() if w in NEGATION[language]]
                ok = all(f" {w} " in h for w in words)
            else:
                ok = f" {normalise(item, 'full', language)} " in h
            miss += not ok
        out[kind] = {"items": len(items), "missed": miss}
    return out


def sum_important(rows: list[dict]) -> dict:
    tot = {}
    for r in rows:
        for k, v in r.items():
            t = tot.setdefault(k, {"items": 0, "missed": 0})
            t["items"] += v["items"]
            t["missed"] += v["missed"]
    return tot


# ---------------------------------------------------------------- speed and cost

def rtf(seconds_of_compute: float, seconds_of_audio: float) -> float:
    """Real-time factor: compute time / audio time. 0.1 means one hour of audio in six minutes."""
    return seconds_of_compute / max(seconds_of_audio, 1e-9)


def cost_per_audio_hour(rtf_value: float, server_usd_per_hour: float) -> float:
    """What one hour of audio costs on a server that runs one transcription at a time."""
    return rtf_value * server_usd_per_hour


# ---------------------------------------------------------------- the comparison table

COLUMNS = ["method", "setting", "slice", "wer", "cer", "order_missed", "rtf", "memory_mb", "usd_per_audio_hour",
           "privacy", "licence"]


class Table:
    """The course's comparison table: one row per method, setting and slice."""

    def __init__(self, rows=None):
        self.rows = list(rows or [])

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f)["rows"])

    def add(self, **row):
        self.rows.append({k: row.get(k) for k in COLUMNS} | {k: v for k, v in row.items() if k not in COLUMNS})

    def where(self, **kw):
        return Table([r for r in self.rows if all(r.get(k) == v for k, v in kw.items())])

    def show(self, columns=None) -> str:
        cols = columns or [c for c in COLUMNS if any(r.get(c) is not None for r in self.rows)]

        def fmt(v):
            if v is None:
                return "-"
            if isinstance(v, float):
                return f"{v:.3f}" if v < 10 else f"{v:.1f}"
            return str(v)

        cells = [[fmt(r.get(c)) for c in cols] for r in self.rows]
        widths = [max([len(c)] + [len(row[i]) for row in cells]) for i, c in enumerate(cols)]
        lines = ["  ".join(c.ljust(w) for c, w in zip(cols, widths))]
        lines += ["  ".join(v.ljust(w) for v, w in zip(row, widths)) for row in cells]
        return "\n".join(lines)

    def __str__(self):
        return self.show()
