"""The returns inspector: a small PatchCore. A ResNet-18 (ONNX) turns a photo into 784 patch vectors; the score is
the largest distance from a patch to its nearest patch in a memory of good candles. Two lines turn the score into
pass, check or fail."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


def preprocess(img, size=224):
    a = np.asarray(img.convert("RGB").resize((size, size), Image.BILINEAR), np.float32) / 255
    return ((a - MEAN) / STD).transpose(2, 0, 1)[None].astype(np.float32)


class Inspector:
    """Loads models/inspector/: model.onnx, bank.npy and config.json (lines and validation statistics)."""

    def __init__(self, folder, threads=1):
        import onnxruntime as ort
        folder = Path(folder)
        self.config = json.loads((folder / "config.json").read_text())
        so = ort.SessionOptions()
        so.intra_op_num_threads = threads
        self.session = ort.InferenceSession(str(folder / "model.onnx"), so, providers=["CPUExecutionProvider"])
        self.bank = np.load(folder / "bank.npy").astype(np.float32)
        self.bank_sq = (self.bank ** 2).sum(1)
        self.version = self.config["version"]

    def score(self, img):
        f = self.session.run(None, {"image": preprocess(img)})[0][0]
        q = f.reshape(f.shape[0], -1).T
        d2 = (q ** 2).sum(1)[:, None] + self.bank_sq[None] - 2 * q @ self.bank.T
        return float(np.sqrt(max(d2.min(1).max(), 0.0)))


def zone(score, check_line, fail_line):
    return "fail" if score >= fail_line else "check" if score >= check_line else "pass"


def confidence(score, check_line, fail_line):
    """How far the score is from the nearest line, as a share of that line (0 in the check zone, at most 1)."""
    if score >= fail_line:
        return round(min(1.0, (score - fail_line) / fail_line), 3)
    if score < check_line:
        return round(min(1.0, (check_line - score) / check_line), 3)
    return 0.0


def photo_problem(img):
    """A reason why the photo cannot be judged (the fallback sends it to a person), or None."""
    if min(img.size) < 100:
        return f"photo too small ({img.size[0]} x {img.size[1]} pixels)"
    m = float(np.asarray(img.convert("L")).mean())
    if m < 25:
        return f"photo too dark (mean brightness {m:.0f} of 255)"
    return None
