"""Read the Larkfield image sets: manifests, costs, checksums."""
import csv
import hashlib
import json
from pathlib import Path

CLASSES = ["bowl", "candle", "chair", "cushion", "lamp", "mug", "plant_pot", "vase"]


def read_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def catalogue(data, split=None):
    rows = read_csv(Path(data) / "catalogue/manifest.csv")
    return [r for r in rows if split is None or r["split"] == split]


def new_studio(data):
    return read_csv(Path(data) / "catalogue/new_studio_manifest.csv")


def returns(data, split=None):
    rows = read_csv(Path(data) / "returns/manifest.csv")
    return [r for r in rows if split is None or r["split"] == split]


def month(data):
    return read_csv(Path(data) / "returns/month_manifest.csv")


def pallets(data, split):
    coco = json.loads((Path(data) / f"pallets/{split}.json").read_text(encoding="utf-8"))
    for im in coco["images"]:
        im["boxes"] = [a["bbox"] for a in coco["annotations"] if a["image_id"] == im["id"]]
    return coco["images"]


def costs(data):
    return json.loads((Path(data) / "costs.json").read_text(encoding="utf-8"))


def check_files(data):
    """(checked, problems): every file in SHA256SUMS must be there with the same checksum."""
    data = Path(data)
    sums = data / "SHA256SUMS"
    if not sums.exists():
        return 0, ["SHA256SUMS is missing"]
    problems, n = [], 0
    for line in sums.read_text().splitlines():
        if not line.strip():
            continue
        h, name = line.split(None, 1)
        p = data / name
        n += 1
        if not p.exists():
            problems.append(f"missing: {name}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != h:
            problems.append(f"changed: {name}")
    return n, problems
