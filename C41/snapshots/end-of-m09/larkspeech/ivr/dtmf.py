"""Keypad tones (DTMF): each key is two tones at once, one low and one high. The Goertzel algorithm measures
the strength of just those eight frequencies in each 20 ms frame of 8 kHz audio."""
import numpy as np

LOW = [697, 770, 852, 941]
HIGH = [1209, 1336, 1477]
KEYS = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["*", "0", "#"]]


def goertzel(frame, sr, freq):
    k = 2 * np.cos(2 * np.pi * freq / sr)
    s1 = s2 = 0.0
    for x in frame:
        s1, s2 = x + k * s1 - s2, s1
    return s1 * s1 + s2 * s2 - k * s1 * s2


_basis = {}


def powers(frame, sr, freqs):
    """The same numbers as goertzel() for each frequency, computed at once with NumPy (faster)."""
    key = (len(frame), sr, tuple(freqs))
    if key not in _basis:
        n = np.arange(len(frame))
        _basis[key] = np.exp(-2j * np.pi * np.outer(freqs, n) / sr)
    return np.abs(_basis[key] @ frame) ** 2


def key_in(frame, sr=8000):
    """The key whose two tones dominate this frame, or None."""
    frame = np.asarray(frame, dtype=np.float64)
    energy = float(np.dot(frame, frame)) + 1e-12
    p = powers(frame, sr, LOW + HIGH)
    lows, highs = p[:4], p[4:]
    i, j = int(np.argmax(lows)), int(np.argmax(highs))
    n = len(frame)
    share = (lows[i] + highs[j]) * 2 / n / energy  # share of the frame's energy in the two tones
    if share < 0.6 or lows[i] < 4 * np.sort(lows)[-2] or highs[j] < 4 * np.sort(highs)[-2]:
        return None
    return KEYS[i][j]


class Detector:
    """Feed 20 ms frames; a key counts once when it is present in two frames in a row."""

    def __init__(self, sr=8000):
        self.sr, self.last, self.count, self.down = sr, None, 0, False

    def feed(self, frame):
        k = key_in(frame, self.sr)
        if k and k == self.last:
            self.count += 1
        else:
            self.count = 1 if k else 0
        self.last = k
        if k and self.count == 2 and not self.down:
            self.down = True
            return k
        if not k:
            self.down = False
        return None


def tones(keys, sr=8000, on=0.1, off=0.1):
    """The audio of keys pressed on a phone (for tests and for the test phone)."""
    out = []
    lo = {k: LOW[r] for r, row in enumerate(KEYS) for k in row}
    hi = {k: HIGH[c] for row in KEYS for c, k in enumerate(row)}
    for k in keys:
        t = np.arange(int(sr * on)) / sr
        out += [0.3 * (np.sin(2 * np.pi * lo[k] * t) + np.sin(2 * np.pi * hi[k] * t)), np.zeros(int(sr * off))]
    return np.concatenate(out).astype(np.float32)
