"""route agreement: how often Chloé and Grace gave the same route to the same messages (raw agreement and
Cohen's kappa), and where they disagree most."""

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from larkroute import data


def agreement(df: pd.DataFrame, a="label_chloe", b="label_grace") -> dict:
    same = df[a] == df[b]
    return {"messages": len(df), "agreement": round(same.mean(), 3), "kappa": round(cohen_kappa_score(df[a], df[b]), 3)}


def run(args):
    df = pd.read_csv(data.data_dir() / "double_labelled.csv")
    s = agreement(df)
    print(f"{s['messages']} messages labelled twice: agreement {s['agreement']:.1%}, Cohen's kappa {s['kappa']:.3f}")
    rows = []
    for route in sorted(set(df["label_chloe"]) | set(df["label_grace"])):
        m = (df["label_chloe"] == route) | (df["label_grace"] == route)
        rows.append({"route": route, "messages": int(m.sum()),
                     "disagree": round((df.loc[m, "label_chloe"] != df.loc[m, "label_grace"]).mean(), 3)})
    print("Disagreement on the messages that either person gave this route:")
    print(pd.DataFrame(rows).sort_values("disagree", ascending=False).to_string(index=False))
    print("Chloé (rows) against Grace (columns):")
    print(pd.crosstab(df["label_chloe"], df["label_grace"]).to_string())


def add(sub):
    p = sub.add_parser("agreement", help="agreement and Cohen's kappa of the two labellers")
    p.set_defaults(func=run)
