"""Where the data, the models and the outputs are."""
import os
from pathlib import Path


def _find(env, marker, explicit=None):
    if explicit:
        p = Path(explicit)
        if not (p / marker).exists():
            raise FileNotFoundError(f"{p / marker} not found")
        return p
    if os.environ.get(env):
        return Path(os.environ[env])
    for p in (Path("data"), Path("../data"), Path("../../data")):
        if (p.parent / p.name / marker).exists():
            return p.resolve()
    raise FileNotFoundError(f"no data folder found (set {env}, or copy the course's data folder here)")


def data_dir(explicit=None):
    return _find("LARKVISION_DATA", "catalogue/manifest.csv", explicit)


def models_dir():
    if os.environ.get("LARKVISION_MODELS"):
        return Path(os.environ["LARKVISION_MODELS"])
    for p in (Path("models"), Path("../models"), Path("../../models")):
        if (p / "inspector").exists():
            return p.resolve()
    raise FileNotFoundError("no models folder found (set LARKVISION_MODELS, or copy the course's models folder here)")


def outputs_dir():
    p = Path(os.environ.get("LARKVISION_OUTPUTS", "outputs"))
    p.mkdir(parents=True, exist_ok=True)
    return p
