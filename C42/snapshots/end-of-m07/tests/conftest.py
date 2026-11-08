"""A tiny fake data folder that looks like the course's (made by code in a few seconds), so the tests need neither
the real images nor a model."""
import base64
import csv
import hashlib
import json
import zlib

import numpy as np
import pytest
from PIL import Image, ImageDraw

CLASSES = ["bowl", "candle", "chair", "cushion", "lamp", "mug", "plant_pot", "vase"]
COLOURS = {"bowl": (230, 230, 230), "candle": (250, 200, 60), "chair": (120, 70, 30), "cushion": (200, 60, 120),
           "lamp": (250, 140, 0), "mug": (40, 90, 200), "plant_pot": (40, 160, 60), "vase": (90, 40, 160)}


def _csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def _photo(colour, size=64, seed=0):
    rng = np.random.default_rng(seed)
    a = np.full((size, size, 3), 128, np.float32)
    a[size // 4:3 * size // 4, size // 4:3 * size // 4] = colour
    a += rng.normal(0, 6, a.shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def _candles(damaged, seed):
    img = Image.new("RGB", (160, 146), (60, 40, 30))
    d = ImageDraw.Draw(img)
    for cx, cy in ((40, 36), (120, 36), (40, 110), (120, 110)):
        d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(245, 225, 190))
    mask = Image.new("L", img.size, 0)
    if damaged:
        d.ellipse([110, 100, 122, 112], fill=(60, 60, 60))
        ImageDraw.Draw(mask).ellipse([110, 100, 122, 112], fill=255)
    return img, mask


@pytest.fixture(scope="session")
def data(tmp_path_factory):
    root = tmp_path_factory.mktemp("data")
    rng = np.random.default_rng(0)
    cat, n = [], 0
    for split, k in (("train", 6), ("val", 2), ("test", 3)):
        for c in CLASSES:
            for i in range(k):
                iid = f"P-{c[:3]}{split[:2]}{i}"
                f = f"catalogue/{split}/{c}/{iid}.jpg"
                (root / f).parent.mkdir(parents=True, exist_ok=True)
                _photo(COLOURS[c], seed=n).save(root / f)
                n += 1
                cat.append({"image_id": iid, "file": f, "split": split, "label": c, "source_id": iid,
                            "source_url": "https://example.org", "licence": "CC BY 2.0", "author": "test",
                            "synthetic": "no", "note": ""})
    # one planted label error: a plant pot labelled vase
    err = next(r for r in cat if r["split"] == "train" and r["label"] == "plant_pot")
    err["label"] = "vase"
    _csv(root / "catalogue/manifest.csv", cat)
    studio = [dict(r, split="new_studio") for r in cat if r["split"] == "test"]
    _csv(root / "catalogue/new_studio_manifest.csv", studio)
    ret = []
    for split, (g, b) in (("train", (6, 2)), ("val", (8, 2)), ("test", (8, 2))):
        for i in range(g + b):
            dmg = i >= g
            iid = f"R-{split[:2]}{i:03d}"
            img, mask = _candles(dmg, i)
            f = f"returns/{split}/{iid}.jpg"
            (root / f).parent.mkdir(parents=True, exist_ok=True)
            img.save(root / f)
            mf = ""
            if dmg:
                mf = f"returns/{split}/masks/{iid}.png"
                (root / mf).parent.mkdir(parents=True, exist_ok=True)
                mask.save(root / mf)
            ret.append({"item_id": iid, "file": f, "split": split, "status": "damaged" if dmg else "good",
                        "damage": "different colour spot" if dmg else "", "mask_file": mf, "source_file": "",
                        "source_mask_pixels": "", "source_url": "", "licence": "CC BY 4.0", "author": "test",
                        "synthetic": "no", "note": "", "day": ""})
    _csv(root / "returns/manifest.csv", ret)
    month = []
    for i in range(8):
        iid = f"R-mo{i:03d}"
        img, _ = _candles(i == 7, 100 + i)
        f = f"returns/month/{iid}.jpg"
        (root / f).parent.mkdir(parents=True, exist_ok=True)
        img.save(root / f)
        month.append({"item_id": iid, "file": f, "day": f"2026-03-{(i * 4) % 30 + 1:02d}", "source_url": "",
                      "licence": "CC BY 4.0", "author": "test", "synthetic": "no", "note": ""})
    _csv(root / "returns/month_manifest.csv", month)
    images, anns, aid = [], [], 1
    for k, crowd in enumerate(("loose", "medium", "tight")):
        f = f"pallets/test/S-{k + 1:03d}.jpg"
        (root / f).parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (200, 150), (180, 180, 180)).save(root / f)
        boxes = [[10 + 40 * j, 50, 30, 30] for j in range(k + 2)]
        images.append({"id": k + 1, "scene_id": f"S-{k + 1:03d}", "file_name": f, "width": 200, "height": 150,
                       "crowding": crowd, "count": len(boxes)})
        for b in boxes:
            anns.append({"id": aid, "image_id": k + 1, "category_id": 1, "bbox": b, "area": 900,
                         "segmentation": [[b[0], b[1], b[0] + 30, b[1], b[0] + 30, b[1] + 30, b[0], b[1] + 30]]})
            aid += 1
    (root / "pallets/test.json").write_text(json.dumps({"images": images, "annotations": anns}))
    preds = []
    for im in images:
        for a in [a for a in anns if a["image_id"] == im["id"]]:
            preds.append({"scene_id": im["scene_id"], "score": 0.9, "box": a["bbox"]})
            preds.append({"scene_id": im["scene_id"], "score": 0.6, "box": [a["bbox"][0] + 2, a["bbox"][1], 30, 30]})
    (root / "predictions").mkdir()
    (root / "predictions/pallets_fasterrcnn_finetuned_40.json").write_text(json.dumps(preds))
    scores = {r["item_id"]: (0.9 if r["status"] == "damaged" else 0.1 + 0.02 * i) for i, r in enumerate(ret)}
    (root / "predictions/returns_small_patchcore.json").write_text(json.dumps(scores))
    cust = [{"photo_id": "C-" + r["image_id"][2:], "file": "", "catalogue_image_id": r["image_id"], "label": r["label"],
             "licence": "CC BY 2.0", "author": "test", "source_url": "", "synthetic": "yes", "note": ""}
            for r in cat if r["split"] == "test"]
    _csv(root / "customer_photos/manifest.csv", cust)
    (root / "embeddings").mkdir()
    centres = {c: rng.normal(0, 1, 16) for c in CLASSES}
    for kind in ("clip", "dinov2", "resnet18"):
        emb = {}
        for r in cat:
            true = "plant_pot" if r is err else r["label"]
            emb[r["image_id"]] = centres[true] + rng.normal(0, 0.3, 16)
        for cphoto in cust:
            emb[cphoto["photo_id"]] = emb[cphoto["catalogue_image_id"]] + rng.normal(0, 0.05, 16)
        np.savez(root / f"embeddings/{kind}.npz", **emb)
    (root / "recordings").mkdir()
    labels = [{"image_id": r["image_id"], "product_type": r["label"], "main_colour": "white", "material": "ceramic"}
              for r in cat if r["split"] == "test"][:4]
    _csv(root / "recordings/attribute_labels.csv", labels)
    recs = [{"task": "attributes", "id": x["image_id"], "model": "fake", "parsed": {
        "product_type": x["product_type"], "main_colour": "white" if i else "red", "material": "ceramic"}}
            for i, x in enumerate(labels)]
    recs += [{"task": "count", "id": im["scene_id"], "model": "fake", "parsed": {"boxes": im["count"] + 1}}
             for im in images]
    recs += [{"task": "inspect", "id": r["item_id"], "model": "fake", "parsed": {"damaged": r["status"] == "damaged"}}
             for r in ret if r["split"] == "test"]
    (root / "recordings/vlm-hosted.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    (root / "costs.json").write_text(json.dumps({"damaged_sold_as_new": 45.0, "good_marked_damaged": 28.0,
                                                 "check_by_a_person": 0.5, "checks_per_day": 100,
                                                 "returns_per_day": 600}))
    (root / "comparison_table.json").write_text(json.dumps({"rows": [
        {"task": "catalogue", "method": "colour histogram + 5-NN", "setting": "catalogue test", "metric": "accuracy",
         "value": 0.3, "worst": "candle", "worst_value": 0.0, "ms_per_image": 0.8, "model_mb": 0,
         "labelled_images": 453, "licence": "none", "label": "measured"}]}))
    key = {"label_errors": [{"image_id": err["image_id"], "true_label": "plant_pot", "given_label": "vase"}],
           "duplicates": []}
    (root / "sealed-key.txt").write_text(base64.b64encode(zlib.compress(json.dumps(key).encode())).decode())
    lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}"
             for p in sorted(root.rglob("*")) if p.is_file()]
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    return root


@pytest.fixture()
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LARKVISION_OUTPUTS", str(tmp_path / "outputs"))
    return tmp_path
