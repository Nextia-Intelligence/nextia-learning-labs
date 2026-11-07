"""Versioned models in models/<version>/: the model file and a card (routes, label version, thresholds, the
messages it learned from, its scores). models/current names the version that the service loads.

A model file is a pickle (joblib): load only model files that you made yourself.
"""

import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"


def label_version(labels: pd.DataFrame) -> str:
    """A short fingerprint of the labels (message ids and routes): the same labels give the same version."""
    rows = "\n".join(f"{m},{r}" for m, r in sorted(zip(labels["message_id"], labels["route"], strict=True)))
    return "labels-" + hashlib.sha256(rows.encode()).hexdigest()[:10]


def save(version: str, model, card: dict) -> Path:
    folder = MODELS / version
    if folder.exists():
        raise SystemExit(f"models/{version} exists: a version is never overwritten. Choose a new version name.")
    folder.mkdir(parents=True)
    joblib.dump(model, folder / "model.joblib")
    (folder / "card.json").write_text(json.dumps({"version": version, **card}, indent=2) + "\n")
    return folder


def load(version: str | None = None):
    version = version or current()
    folder = MODELS / version
    if not folder.exists():
        raise SystemExit(f"No model {version}. Run: route train --version {version}")
    return joblib.load(folder / "model.joblib"), json.loads((folder / "card.json").read_text())


def current() -> str:
    f = MODELS / "current"
    if not f.exists():
        raise SystemExit("No current model. Run: route train --version v1")
    return f.read_text().strip()


def set_current(version: str) -> None:
    MODELS.mkdir(exist_ok=True)
    previous = (MODELS / "current").read_text().strip() if (MODELS / "current").exists() else None
    (MODELS / "current").write_text(version + "\n")
    if previous and previous != version:
        (MODELS / "previous").write_text(previous + "\n")
