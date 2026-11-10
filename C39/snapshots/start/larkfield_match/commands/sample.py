"""match sample: pairs for you to label by hand (Module 1's practice)."""

import sys

import numpy as np
import pandas as pd

from .. import data
from ..paths import out

NAME = "sample"
HELP = "Write N candidate pairs (default 40) to outputs/to_label.csv, for you to label same, different or unsure."


def add(p):
    p.add_argument("--n", type=int, default=40)
    p.add_argument("--seed", type=int, default=7)


def run(args):
    rng = np.random.default_rng(args.seed)
    recs = data.records()
    t = data.truth()
    train = recs[recs.record_id.isin(t[t.split == "train"].record_id)].copy()
    # pairs that look alike: the same last word of the name (after the comma for the garden centres)
    last = train.name.str.replace(r"^([^,]+),.*$", r"\1", regex=True).str.split().str[-1].str.lower()
    train["key"] = last.str[:4]
    groups = [g.record_id.tolist() for _, g in train.groupby("key") if 2 <= len(g) <= 400]
    chosen = set()
    while len(chosen) < args.n:
        g = groups[rng.integers(len(groups))]
        a, b = sorted(rng.choice(g, 2, replace=False))
        chosen.add((a, b))
    by = recs.set_index("record_id")
    rows = []
    for a, b in sorted(chosen):
        ra, rb = by.loc[a], by.loc[b]
        rows.append({"record_l": a, "record_r": b, **{f"{c}_l": ra[c] for c in ["name", "email", "phone",
                     "address", "postcode", "date_of_birth"]}, **{f"{c}_r": rb[c] for c in ["name", "email",
                     "phone", "address", "postcode", "date_of_birth"]}, "label": "", "reason": ""})
    path = out("to_label.csv")
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"Wrote {len(rows)} pairs to {path}. Fill 'label' with same, different or unsure, and a reason.")
    print("Then check your labels with: match sample-check")


class _Check:
    NAME = "sample-check"
    HELP = "Compare your labels in outputs/to_label.csv with the true entities."

    @staticmethod
    def add(p):
        pass

    @staticmethod
    def run(args):
        df = pd.read_csv(out("to_label.csv"), dtype=str, keep_default_na=False)
        ent = data.truth().set_index("record_id").entity_id
        df["true"] = np.where(df.record_l.map(ent) == df.record_r.map(ent), "same", "different")
        lab = df[df.label.isin(["same", "different"])]
        unsure = int((df.label == "unsure").sum())
        right = int((lab.label == lab.true).sum())
        print(f"Labelled {len(lab)} pairs as same or different: {right} agree with the true entities; "
              f"{unsure} unsure; {len(df) - len(lab) - unsure} empty.")
        print(f"True pairs in the sample: {int((df.true == 'same').sum())} of {len(df)}")
        for _, r in lab[lab.label != lab.true].iterrows():
            print(f"  {r.record_l} / {r.record_r}: you said {r.label}, true is {r.true}")


COMMANDS = [sys.modules[__name__], _Check]
