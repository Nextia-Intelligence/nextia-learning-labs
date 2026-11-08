"""Personal data in voice: find card numbers in a transcript, remove them from the text, and beep them in the
audio using the word times. The privacy check proves that no card number is left."""
import json
import re

import numpy as np

from larkspeech.compare import normalise
from larkspeech.numbers import luhn_ok

CARD = "[CARD NUMBER REMOVED]"


def card_numbers(text, language="en", strict=True):
    """Digit runs that look like a card number, after the normalisation guide. strict: 13 to 19 digits that pass
    the Luhn check (few false alarms, but a recogniser that drops or changes one digit hides the card).
    strict=False: any run of 12 or more digits (catches damaged card numbers; order numbers have 6)."""
    runs = re.findall(r"\d+", normalise(text, "full", language))
    if strict:
        return [r for r in runs if 13 <= len(r) <= 19 and luhn_ok(r)]
    return [r for r in runs if len(r) >= 12]


def redact_words(words, language="en", strict=True):
    """words: [(word, start, end)] from the recogniser. Returns (words with the card digits replaced,
    the (start, end) times to beep). A card number is a run of number words whose digits make a card number."""
    out, spans, i = [], [], 0
    norm = [normalise(w, "full", language) for w, _, _ in words]
    while i < len(words):
        j, digits = i, ""
        while j < len(words) and (norm[j].isdigit() or (norm[j] == "" and j > i)):
            digits += norm[j]
            j += 1
        looks_like_card = (13 <= len(digits) <= 19 and luhn_ok(digits)) if strict else len(digits) >= 12
        if j > i and looks_like_card:
            out.append((CARD, words[i][1], words[j - 1][2]))
            spans.append((words[i][1], words[j - 1][2]))
            i = j
        else:
            out.append(words[i])
            i += 1
    return out, spans


def redact_text(text, language="en", strict=False):
    """The transcript without card numbers (digits or number words)."""
    words = [(w, 0.0, 0.0) for w in text.split()]
    red, _ = redact_words(words, language, strict)
    return " ".join(w for w, _, _ in red)


def beep(x, sr, spans, freq=1000, pad=0.15):
    """Replace each span of the audio with a tone, so nobody can hear the digits again."""
    y = x.copy()
    for s, e in spans:
        a, b = max(0, int((s - pad) * sr)), min(len(y), int((e + pad) * sr))
        t = np.arange(b - a) / sr
        y[a:b] = 0.1 * np.sin(2 * np.pi * freq * t)
    return y


# Fields of our JSON records that hold times, durations or IDs, never words that someone said. Their numbers are
# not scanned: a list of turn times ("0.0, 3.21, 3.5, ...") would otherwise read as one long run of digits.
NOT_SPOKEN = {"start", "end", "seconds", "duration", "time", "times", "timeline", "turns", "call_id", "id", "order",
              "orders", "rtf", "real_time_factor", "tokens", "usd"}


def spoken_parts(name, raw):
    """The pieces of a file to scan. A .txt file is one piece. In a .json or .jsonl file, every string is its own
    piece, except in the NOT_SPOKEN fields; numbers are skipped, except whole numbers of 12 digits or more (a card
    number saved as a number). A JSON file that does not parse is scanned as text."""
    if not str(name).endswith((".json", ".jsonl")):
        return [raw]
    try:
        records = [json.loads(raw)] if str(name).endswith(".json") else \
            [json.loads(x) for x in raw.splitlines() if x.strip()]
    except ValueError:
        return [raw]
    parts = []

    def walk(v, key=None):
        if key in NOT_SPOKEN:
            return
        if isinstance(v, dict):
            for k, x in v.items():
                walk(x, k)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str):
            parts.append(v)
        elif isinstance(v, int) and not isinstance(v, bool) and len(str(abs(v))) >= 12:
            parts.append(str(v))

    for r in records:
        walk(r)
    return parts


def privacy_check(texts, language="en", strict=False):
    """Problems: every text that still holds a card number (by default the broad rule: 12 digits or more).
    texts: {name: text} or {name: [pieces]} (each piece is scanned on its own, see spoken_parts)."""
    out = []
    for name, t in texts.items():
        for piece in ([t] if isinstance(t, str) else t):
            out += [(name, n) for n in card_numbers(piece, language, strict)]
    return out
