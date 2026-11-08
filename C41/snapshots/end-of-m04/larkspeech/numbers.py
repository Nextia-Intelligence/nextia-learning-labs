"""Order numbers after recognition: spoken digits to digits, the check digit, and the lookup."""
import re

from larkspeech.compare import normalise


def luhn_ok(number):
    """Larkfield order numbers have 6 digits; the last one is a check digit (Luhn), so most one-digit
    mistakes and most swaps of two neighbours are caught before the lookup."""
    if not number.isdigit() or len(number) < 2:
        return False
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def digits_in(text, language="en"):
    """All digit runs in a transcript after the normalisation guide ("seven four two" -> "742")."""
    return re.findall(r"\d+", normalise(text, "full", language))


def find_order_number(text, language="en", length=6):
    """(number, problem): the 6-digit order number in a caller's words, or a reason why there is none."""
    runs = digits_in(text, language)
    if not runs:
        return None, "no digits"
    best = max(runs, key=len)
    if len(best) < length:
        return best, "too short"
    if len(best) > length:
        return best, "too long"
    if not luhn_ok(best):
        return best, "check digit wrong"
    return best, None


def fix_order_numbers(text, language="en"):
    """Write spoken order numbers as digits inside a transcript (the rest of the text is unchanged)."""
    words = text.split()
    out, run = [], []
    for w in words:
        n = normalise(w, "full", language)
        if n.isdigit() or (n == "oh" and run):
            run.append("0" if n == "oh" else n)
        else:
            if run:
                out.append("".join(run))
                run = []
            out.append(w)
    if run:
        out.append("".join(run))
    return " ".join(out)
