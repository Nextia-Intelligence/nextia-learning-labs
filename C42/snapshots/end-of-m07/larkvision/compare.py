"""The comparison table for the Vision AI course: score every method the same way.

The same file is `compare.py` in the course's labs folder (for the notebooks) and `larkvision/compare.py` in the
image service project. It needs only NumPy (and pandas for `Table.frame`, if pandas is there).

    import compare as cp
    row = cp.classification_row("colour histogram + 5-NN", y_true, y_pred, setting="catalogue test, 160 photos",
                                ms_per_image=0.4, model_mb=0, labelled=563, licence="none (our code)")
    table = cp.Table.load("comparison_table.json")   # the course's measured rows
    table.add(row); table.show(task="catalogue")

Tasks and their main metric:
  catalogue  eight-class product photos      accuracy (worst case: the class with the lowest recall)
  inspect    returned candles, good/damaged  cost per day at Hamid's budget (worst case: the damage type found least)
  count      boxes on pallet photos          mean absolute count error (worst case: the crowding level with most error)
  match      customer photo -> catalogue     recall at 5 (worst case: the class with the lowest recall at 5)
  attributes vision-language answers         accuracy of the attribute (worst case: the attribute with lowest accuracy)
"""
import base64
import json
import math
import zlib
from pathlib import Path

import numpy as np

COLUMNS = ["task", "method", "setting", "metric", "value", "worst", "worst_value", "ms_per_image", "model_mb",
           "labelled_images", "licence", "label"]

# The cost table (assumptions, the same for the whole course; data/costs.json has them too).
COSTS = {"damaged_sold_as_new": 45.0, "good_marked_damaged": 28.0, "check_by_a_person": 0.5, "checks_per_day": 100,
         "returns_per_day": 600}


# ---------------------------------------------------------------- classification

def confusion(y_true, y_pred, labels):
    idx = {c: i for i, c in enumerate(labels)}
    m = np.zeros((len(labels), len(labels)), int)
    for t, p in zip(y_true, y_pred):
        m[idx[t], idx[p]] += 1
    return m


def per_class(y_true, y_pred, labels):
    """precision, recall and F1 for each class."""
    m = confusion(y_true, y_pred, labels)
    out = {}
    for i, c in enumerate(labels):
        tp = m[i, i]
        p = tp / m[:, i].sum() if m[:, i].sum() else 0.0
        r = tp / m[i].sum() if m[i].sum() else 0.0
        out[c] = {"precision": round(float(p), 3), "recall": round(float(r), 3),
                  "f1": round(float(2 * p * r / (p + r)) if p + r else 0.0, 3), "n": int(m[i].sum())}
    return out


def classification_scores(y_true, y_pred, labels=None):
    labels = labels or sorted(set(y_true))
    pc = per_class(y_true, y_pred, labels)
    worst = min(labels, key=lambda c: (pc[c]["recall"], c))
    return {"accuracy": round(float(np.mean(np.asarray(y_true) == np.asarray(y_pred))), 3),
            "macro_f1": round(float(np.mean([pc[c]["f1"] for c in labels])), 3),
            "worst_class": worst, "worst_recall": pc[worst]["recall"], "per_class": pc}


def classification_row(method, y_true, y_pred, setting, ms_per_image, model_mb, labelled, licence, label="measured",
                       task="catalogue"):
    """A row of the comparison table for a classifier. `task` names the table's task column (the course's catalogue,
    or another set, such as "pets" in a case study)."""
    s = classification_scores(list(y_true), list(y_pred))
    return {"task": task, "method": method, "setting": setting, "metric": "accuracy", "value": s["accuracy"],
            "worst": s["worst_class"], "worst_value": s["worst_recall"], "ms_per_image": ms_per_image,
            "model_mb": model_mb, "labelled_images": labelled, "licence": licence, "label": label}


# ---------------------------------------------------------------- inspection: pass, check, fail

def zones(scores, check_line, fail_line):
    """'pass' below check_line, 'fail' at or above fail_line, 'check' between."""
    s = np.asarray(scores, float)
    return np.where(s >= fail_line, "fail", np.where(s >= check_line, "check", "pass"))


def inspection_costs(scores, damaged, check_line, fail_line, costs=COSTS):
    """The daily cost of a pair of lines, scaled to 600 returns a day.

    A damaged item that passes is sold as new; a good item that fails goes to the outlet; every 'check' costs a
    person's minute, and a person is always right.
    """
    z = zones(scores, check_line, fail_line)
    d = np.asarray(damaged, bool)
    n = len(d)
    scale = costs["returns_per_day"] / n
    missed = int(((z == "pass") & d).sum())
    lost = int(((z == "fail") & ~d).sum())
    checks = int((z == "check").sum())
    per_day = {"checks": checks * scale, "damaged_sold_as_new": missed * scale, "good_marked_damaged": lost * scale}
    cost = (per_day["damaged_sold_as_new"] * costs["damaged_sold_as_new"]
            + per_day["good_marked_damaged"] * costs["good_marked_damaged"]
            + per_day["checks"] * costs["check_by_a_person"])
    return {"items": n, "damaged": int(d.sum()), "missed": missed, "good_failed": lost, "checks": checks,
            "checks_per_day": round(per_day["checks"], 1),
            "damaged_sold_as_new_per_day": round(per_day["damaged_sold_as_new"], 1),
            "good_marked_damaged_per_day": round(per_day["good_marked_damaged"], 1),
            "cost_per_day": round(cost, 1), "over_budget": per_day["checks"] > costs["checks_per_day"]}


def choose_lines(scores, damaged, costs=COSTS, grid=200):
    """The cheapest (check_line, fail_line) whose checks stay inside the daily budget. Use validation scores only."""
    s = np.asarray(scores, float)
    qs = np.unique(np.quantile(s, np.linspace(0, 1, grid + 1)))
    qs = np.append(qs, s.max() + 1e-9)
    best = None
    for i, lo in enumerate(qs):
        for hi in qs[i:]:
            c = inspection_costs(s, damaged, lo, hi, costs)
            if c["over_budget"]:
                continue
            key = (c["cost_per_day"], c["checks_per_day"])
            if best is None or key < best[0]:
                best = (key, float(lo), float(hi), c)
    _, lo, hi, c = best
    return {"check_line": lo, "fail_line": hi, **c}


def roc_auc(scores, damaged):
    s = np.asarray(scores, float)
    d = np.asarray(damaged, bool)
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s))
    ranks[order] = np.arange(1, len(s) + 1)
    for v in np.unique(s):  # ties get the average rank
        m = s == v
        ranks[m] = ranks[m].mean()
    npos, nneg = d.sum(), (~d).sum()
    return round(float((ranks[d].sum() - npos * (npos + 1) / 2) / (npos * nneg)), 3)


def inspection_row(method, val_scores, val_damaged, test_scores, test_damaged, test_types, setting, ms_per_image,
                   model_mb, labelled, licence, label="measured"):
    """Lines chosen on validation, cost measured on test. Worst = the damage type that passes most often."""
    lines = choose_lines(val_scores, val_damaged)
    c = inspection_costs(test_scores, test_damaged, lines["check_line"], lines["fail_line"])
    z = zones(test_scores, lines["check_line"], lines["fail_line"])
    by_type = {}
    for zz, t, d in zip(z, test_types, test_damaged):
        if d:
            for one in t.split("; "):
                by_type.setdefault(one, []).append(zz != "pass")
    worst = min(by_type, key=lambda k: (np.mean(by_type[k]), k)) if by_type else ""
    return {"task": "inspect", "method": method, "setting": setting, "metric": "cost per day (CAD)",
            "value": c["cost_per_day"], "worst": worst,
            "worst_value": round(float(np.mean(by_type[worst])), 3) if worst else None,
            "ms_per_image": ms_per_image, "model_mb": model_mb, "labelled_images": labelled, "licence": licence,
            "label": label, "auroc": roc_auc(test_scores, test_damaged),
            "lines": [lines["check_line"], lines["fail_line"]],
            "test": c}


# ---------------------------------------------------------------- boxes, IoU, counting

def iou(a, b):
    """IoU of two boxes [x, y, w, h]."""
    ax1, ay1, bx1, by1 = a[0] + a[2], a[1] + a[3], b[0] + b[2], b[1] + b[3]
    iw = max(0.0, min(ax1, bx1) - max(a[0], b[0]))
    ih = max(0.0, min(ay1, by1) - max(a[1], b[1]))
    inter = iw * ih
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def nms(boxes, scores, iou_threshold=0.5):
    """Non-maximum suppression: keep the best box, drop boxes that overlap it more than the threshold."""
    order = list(np.argsort(-np.asarray(scores), kind="mergesort"))
    keep = []
    while order:
        i = order.pop(0)
        keep.append(int(i))
        order = [j for j in order if iou(boxes[i], boxes[j]) <= iou_threshold]
    return keep


def average_precision(gts, preds, iou_threshold=0.5, area_range=None):
    """AP for one class. gts: {image_id: [box]}, preds: [(image_id, score, box)]. Boxes [x, y, w, h].

    area_range=(lo, hi) keeps ground-truth boxes with lo <= area < hi; a prediction that matches no box of that
    size range is ignored if it matches a box outside it (as COCO does)."""
    def in_range(b):
        return area_range is None or area_range[0] <= b[2] * b[3] < area_range[1]
    n_gt = sum(1 for bs in gts.values() for b in bs if in_range(b))
    if n_gt == 0:
        return float("nan")
    used = {k: [False] * len(v) for k, v in gts.items()}
    tps, fps = [], []
    for img, _, box in sorted(preds, key=lambda p: -p[1]):
        best, bi = 0.0, -1
        for j, g in enumerate(gts.get(img, [])):
            if used[img][j]:
                continue
            o = iou(box, g)
            if o > best:
                best, bi = o, j
        if best >= iou_threshold:
            used[img][bi] = True
            if in_range(gts[img][bi]):
                tps.append(1)
                fps.append(0)
            continue
        if area_range is not None and not in_range(box):
            continue
        tps.append(0)
        fps.append(1)
    tp, fp = np.cumsum(tps), np.cumsum(fps)
    rec = tp / n_gt if len(tp) else np.array([0.0])
    prec = tp / np.maximum(tp + fp, 1) if len(tp) else np.array([0.0])
    ap = 0.0
    for r in np.linspace(0, 1, 101):  # 101-point interpolation, as COCO
        p = prec[rec >= r]
        ap += (p.max() if len(p) else 0.0) / 101
    return round(float(ap), 3)


def map_50_95(gts, preds, area_range=None):
    return round(float(np.mean([average_precision(gts, preds, t, area_range) for t in np.arange(0.5, 0.96, 0.05)])), 3)


SIZES = {"small": (0, 32 ** 2), "medium": (32 ** 2, 96 ** 2), "large": (96 ** 2, 1e12)}


def count_scores(true_counts, pred_counts, crowding):
    t, p = np.asarray(true_counts, float), np.asarray(pred_counts, float)
    by = {}
    for c in sorted(set(crowding)):
        m = np.asarray(crowding) == c
        by[c] = {"mae": round(float(np.abs(t[m] - p[m]).mean()), 2), "bias": round(float((p[m] - t[m]).mean()), 2),
                 "scenes": int(m.sum())}
    worst = max(by, key=lambda c: by[c]["mae"])
    return {"mae": round(float(np.abs(t - p).mean()), 2), "bias": round(float((p - t).mean()), 2),
            "exact": round(float((np.round(p) == t).mean()), 3), "by_crowding": by, "worst": worst}


def count_row(method, true_counts, pred_counts, crowding, setting, ms_per_image, model_mb, labelled, licence,
              label="measured", **extra):
    s = count_scores(true_counts, pred_counts, crowding)
    return {"task": "count", "method": method, "setting": setting, "metric": "count error (MAE, boxes)",
            "value": s["mae"], "worst": s["worst"], "worst_value": s["by_crowding"][s["worst"]]["mae"],
            "ms_per_image": ms_per_image, "model_mb": model_mb, "labelled_images": labelled, "licence": licence,
            "label": label, "detail": s, **extra}


# ---------------------------------------------------------------- matching

def recall_at_k(ranked, truth, k):
    """ranked: list of lists of catalogue IDs (best first); truth: the right ID for each query."""
    return round(float(np.mean([t in r[:k] for r, t in zip(ranked, truth)])), 3)


def match_row(method, ranked, truth, labels, setting, ms_per_image, model_mb, licence, label="measured"):
    hit = {}
    for r, t, c in zip(ranked, truth, labels):
        hit.setdefault(c, []).append(t in r[:5])
    worst = min(hit, key=lambda c: (np.mean(hit[c]), c))
    return {"task": "match", "method": method, "setting": setting, "metric": "recall at 5",
            "value": recall_at_k(ranked, truth, 5), "worst": worst, "worst_value": round(float(np.mean(hit[worst])), 3),
            "ms_per_image": ms_per_image, "model_mb": model_mb, "labelled_images": 0, "licence": licence,
            "label": label, "recall_at_1": recall_at_k(ranked, truth, 1)}


# ---------------------------------------------------------------- masks

def mask_iou(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 1.0


def dice(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    s = a.sum() + b.sum()
    return float(2 * (a & b).sum() / s) if s else 1.0


# ---------------------------------------------------------------- the table

class Table:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    @classmethod
    def load(cls, path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8"))["rows"])

    def save(self, path):
        Path(path).write_text(json.dumps({"columns": COLUMNS, "rows": self.rows}, indent=1) + "\n", encoding="utf-8")

    def add(self, row):
        self.rows = [r for r in self.rows if not (r["task"] == row["task"] and r["method"] == row["method"]
                                                  and r["setting"] == row["setting"])]
        self.rows.append(row)
        return self

    def select(self, task=None):
        return [r for r in self.rows if task is None or r["task"] == task]

    def frame(self, task=None):
        import pandas as pd
        return pd.DataFrame([{c: r.get(c) for c in COLUMNS} for r in self.select(task)], columns=COLUMNS)

    def show(self, task=None, columns=("method", "setting", "value", "worst", "worst_value", "ms_per_image",
                                       "model_mb", "labelled_images", "licence")):
        rows = self.select(task)
        if not rows:
            print("(no rows)")
            return
        if task:
            print(f"{task}: {rows[0]['metric']}")
        cells = [[_fmt(r.get(c)) for c in columns] for r in rows]
        widths = [max(len(c), *(len(x[i]) for x in cells)) for i, c in enumerate(columns)]
        print("  ".join(c.ljust(w) for c, w in zip(columns, widths)))
        for x in cells:
            print("  ".join(v.ljust(w) for v, w in zip(x, widths)))


def _fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        if math.isnan(v):
            return "-"
        return f"{v:.3f}" if abs(v) < 10 else f"{v:.1f}"
    return str(v)


# ---------------------------------------------------------------- the sealed key

def reveal(path="data/sealed-key.txt"):
    """The planted label errors and duplicates of the catalogue. Not secret: it is there to score your search."""
    return json.loads(zlib.decompress(base64.b64decode(Path(path).read_text().strip())))
