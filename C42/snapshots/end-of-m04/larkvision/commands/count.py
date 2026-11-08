"""`vision count`: count boxes on the pallet photos from recorded detector boxes, or with the label rule."""
import json
from pathlib import Path

import numpy as np

from larkvision import data as D
from larkvision.commands.compare import add_row
from larkvision.compare import average_precision, count_row, count_scores, iou, nms
from larkvision.paths import data_dir

METHODS = {
    "finetuned-40": "fasterrcnn_finetuned_40", "finetuned-10": "fasterrcnn_finetuned_10",
    "owlv2": "owlv2_a_cardboard_box", "rtdetr-coco": "rtdetr_coco", "fasterrcnn-coco": "fasterrcnn_coco",
}


def register(sub):
    p = sub.add_parser("count", help="count the boxes on the pallet test photos")
    p.add_argument("--method", choices=sorted(METHODS) + ["label-rule"], default="finetuned-40")
    p.add_argument("--score", type=float, default=0.5, help="keep boxes with at least this score")
    p.add_argument("--nms", type=float, default=None, help="non-maximum suppression at this IoU (default: none)")
    p.set_defaults(run=run)


def label_rule(path):
    """Count the white labels and divide by 0.7 (7 boxes in 10 have a label)."""
    from PIL import Image
    from scipy import ndimage
    a = np.asarray(Image.open(path).convert("RGB"), float)
    white = a.min(2) > 200
    lab, n = ndimage.label(white)
    sizes = ndimage.sum(white, lab, range(1, n + 1))
    return int(round((np.asarray(sizes) >= 12).sum() / 0.7))


def merged(images, preds):
    """Kept boxes that cover two true boxes at once (IoU >= 0.6 with their union, < 0.4 with each)."""
    n = 0
    for im in images:
        G = im["boxes"]
        for pb in preds.get(im["scene_id"], []):
            for i in range(len(G)):
                for j in range(i + 1, len(G)):
                    a, b = G[i], G[j]
                    x0, y0 = min(a[0], b[0]), min(a[1], b[1])
                    u = [x0, y0, max(a[0] + a[2], b[0] + b[2]) - x0, max(a[1] + a[3], b[1] + b[3]) - y0]
                    if iou(pb, u) >= 0.6 and iou(pb, a) < 0.4 and iou(pb, b) < 0.4:
                        n += 1
    return n


def run(args):
    d = data_dir(args.data)
    images = D.pallets(d, "test")
    truth = [im["count"] for im in images]
    crowd = [im["crowding"] for im in images]
    if args.method == "label-rule":
        counts = [label_rule(Path(d) / im["file_name"]) for im in images]
        s = count_scores(truth, counts, crowd)
        name, ap, m = "rule: count the white labels, divide by 0.7", None, None
    else:
        raw = json.loads((Path(d) / f"predictions/pallets_{METHODS[args.method]}.json").read_text())
        kept = {}
        for im in images:
            P = [p for p in raw if p["scene_id"] == im["scene_id"] and p["score"] >= args.score]
            if args.nms is not None:
                P = [P[i] for i in nms([p["box"] for p in P], [p["score"] for p in P], args.nms)]
            kept[im["scene_id"]] = [p["box"] for p in P]
        counts = [len(kept[im["scene_id"]]) for im in images]
        s = count_scores(truth, counts, crowd)
        gts = {im["scene_id"]: im["boxes"] for im in images}
        ap = average_precision(gts, [(p["scene_id"], p["score"], p["box"]) for p in raw], 0.5)
        m = merged(images, kept)
        name = f"{args.method} (score >= {args.score}" + (f", NMS {args.nms})" if args.nms is not None else ")")
    print(f"{name}: count error {s['mae']} boxes a photo (bias {s['bias']:+}), exact on {s['exact']:.0%} of photos")
    for k, v in s["by_crowding"].items():
        print(f"  {k:6s} {v['scenes']} photos: error {v['mae']}, bias {v['bias']:+}")
    if ap is not None:
        print(f"  AP at IoU 0.5: {ap:.3f}; kept boxes that cover two boxes: {m}")
    add_row(count_row(name, truth, counts, crowd, "pallets test", None, None, None, "-"))
