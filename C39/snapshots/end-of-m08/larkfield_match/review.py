"""Human review (Module 8, lesson 2): the queue, what the reviewer sees, and her decisions as labels.

The queue is outputs/review_queue.csv. A reviewer can check `capacity` pairs a day (300 for Ivana, an
assumption in data/costs.json). In this course a simulated reviewer decides from the true answer and makes a
mistake on `error` of the pairs (2% by default, an assumption). Decisions go to outputs/review_labels.csv:
"same" merges the two entities (logged), "different" keeps them apart for ever (outputs/cannot_link.csv).
"""

import numpy as np
import pandas as pd

from . import data, golden, incremental
from .paths import out

FIELDS = ["name", "email", "phone", "address", "postcode", "date_of_birth"]


def queue():
    p = out("review_queue.csv")
    if not p.exists():
        return pd.DataFrame(columns=["record_id_l", "record_id_r", "probability", "reason", "day"])
    q = pd.read_csv(p, dtype={"record_id_l": str, "record_id_r": str})
    done = labels()
    if len(done):
        key = set(zip(done.record_id_l, done.record_id_r))
        q = q[[(a, b) not in key for a, b in zip(q.record_id_l, q.record_id_r)]]
    return q.drop_duplicates(["record_id_l", "record_id_r"])


def labels():
    p = out("review_labels.csv")
    return pd.read_csv(p, dtype=str).astype({"label": int}) if p.exists() else \
        pd.DataFrame(columns=["record_id_l", "record_id_r", "label", "decided_by"])


def raw_view():
    """Every record as written, also the daily ones (for the reviewer's screen)."""
    base = data.records()
    days = []
    for d in range(1, 8):
        p = incremental.data_dir() / "daily" / f"day-{d}.csv"
        if p.exists():
            df = pd.read_csv(p, dtype=str, keep_default_na=False)
            name = (df.first_name + " " + df.last_name).str.strip()
            name = name.where(name != "", df.full_name)
            addr = (df.address + ", " + df.city + " " + df.province).str.strip(", ")
            days.append(pd.DataFrame({"record_id": df.record_id, "source": df.source, "name": name,
                                      "email": df.email, "phone": df.phone, "address": addr,
                                      "postcode": df.postcode, "date_of_birth": df.date_of_birth}))
    return pd.concat([base] + days, ignore_index=True).set_index("record_id")


def show(n=3):
    """What the reviewer sees: the two records field by field, with the differences marked."""
    q = queue().sort_values("probability", ascending=False).head(n)
    view = raw_view()
    lines = []
    for r in q.itertuples():
        a, b = view.loc[r.record_id_l], view.loc[r.record_id_r]
        lines.append(f"{r.record_id_l} / {r.record_id_r}   probability {r.probability:.2f}   ({r.reason})")
        for f in FIELDS:
            mark = "  " if a[f] == b[f] else "≠ "
            lines.append(f"  {mark}{f:<14} {a[f] or '-':<38} {b[f] or '-'}")
    return "\n".join(lines)


def simulate(capacity=300, error=0.02, seed=1):
    """A simulated reviewer decides the `capacity` most likely pairs of the queue."""
    q = queue().sort_values("probability", ascending=False).head(capacity)
    truth = dict(zip(*incremental.all_truth().T.values))
    rng = np.random.default_rng(seed + len(labels()))
    same = np.array([truth[a] == truth[b] for a, b in zip(q.record_id_l, q.record_id_r)], dtype=int)
    flip = rng.random(len(q)) < error
    decided = np.where(flip, 1 - same, same)
    lab = pd.DataFrame({"record_id_l": q.record_id_l, "record_id_r": q.record_id_r, "label": decided,
                        "decided_by": "simulated reviewer"})
    p = out("review_labels.csv")
    lab.to_csv(p, mode="a", header=not p.exists(), index=False)
    apply(lab)
    return {"decided": len(lab), "same": int(decided.sum()), "different": int(len(lab) - decided.sum()),
            "reviewer_mistakes": int(flip.sum()), "left_in_queue": len(queue())}


def apply(lab):
    """'same' merges the two entities (the older ID stays); 'different' is written to cannot_link.csv."""
    ents = golden.load_entities()
    e = dict(zip(ents.record_id, ents.entity_id))
    for r in lab.itertuples():
        if r.record_id_l not in e or r.record_id_r not in e:
            continue
        if r.label == 1 and e[r.record_id_l] != e[r.record_id_r]:
            keep, drop = sorted([e[r.record_id_l], e[r.record_id_r]])
            for k, v in e.items():
                if v == drop:
                    e[k] = keep
            golden.log("merge", entities=[keep, drop], kept=keep, by="review")
    golden.save_entities(pd.DataFrame({"record_id": list(e), "entity_id": list(e.values())}))
    diff = lab[lab.label == 0][["record_id_l", "record_id_r"]]
    if len(diff):
        p = out("cannot_link.csv")
        diff.to_csv(p, mode="a", header=not p.exists(), index=False)
