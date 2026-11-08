"""Where the data, the models and the outputs are."""
import os
from pathlib import Path


def data_dir(explicit=None):
    marker = "calls/calls.jsonl"
    if explicit:
        p = Path(explicit)
        if not (p / marker).exists():
            raise FileNotFoundError(f"{p / marker} not found")
        return p
    if os.environ.get("LARKSPEECH_DATA"):
        return Path(os.environ["LARKSPEECH_DATA"])
    for p in (Path("data"), Path("../data"), Path("../../data")):
        if (p / marker).exists():
            return p.resolve()
    raise FileNotFoundError("no data folder found (set LARKSPEECH_DATA, or copy the course's data folder here)")


def models_dir():
    """Downloaded models (voices, speaker model, Vosk). Created when needed."""
    if os.environ.get("LARKSPEECH_MODELS"):
        p = Path(os.environ["LARKSPEECH_MODELS"])
    else:
        p = next((q.resolve() for q in (Path("models"), Path("../models"), Path("../../models")) if q.exists()),
                 Path("models").resolve())
    p.mkdir(parents=True, exist_ok=True)
    return p


def outputs_dir():
    p = Path(os.environ.get("LARKSPEECH_OUTPUTS", "outputs"))
    p.mkdir(parents=True, exist_ok=True)
    return p
