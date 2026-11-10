"""search judge: judge results yourself, and measure agreement between judges."""

from pathlib import Path

import pandas as pd

from .. import data, judge, runs
from ..paths import outputs_dir

NAME = "judge"
HELP = "Judge results (sample), then compare your grades with the WANDS judges or the model's (agree)."


def add(p):
    p.add_argument("action", choices=["sample", "agree", "llm"],
                   help="sample: write 30 results to judge; agree FILE: compare your grades with the WANDS judges; "
                        "llm: compare the recorded model labels with the WANDS judges")
    p.add_argument("file", nargs="?", help="the judged file for agree (default outputs/judge_sample.csv)")
    p.add_argument("--run", default="bm25")
    p.add_argument("--seed", type=int, default=1)


def run(args):
    if args.action == "sample":
        df = judge.sample(runs.get(args.run), seed=args.seed)
        out = outputs_dir() / "judge_sample.csv"
        df.to_csv(out, index=False)
        print(f"Wrote {len(df)} results of {df['query_id'].nunique()} queries to {out}.")
        print("Fill the column your_grade with 2 (exact), 1 (partial) or 0 (irrelevant), following "
              "docs/judging-guidelines.md. Then run: search judge agree")
        return
    if args.action == "agree":
        path = Path(args.file) if args.file else outputs_dir() / "judge_sample.csv"
        df = pd.read_csv(path, keep_default_na=False)
        df = df[df["your_grade"].astype(str).str.strip() != ""]
        j = data.judgments()
        df = df[[p in j.get(q, {}) for q, p in zip(df["query_id"], df["product_id"])]]
        if df.empty:
            raise SystemExit("No judged rows with a WANDS judgment yet: fill your_grade first.")
        a = [j[q][p] for q, p in zip(df["query_id"], df["product_id"])]
        r = judge.agreement(a, df["your_grade"].astype(int))
        print(f"You and the WANDS judges on {r['pairs']} results (A = WANDS, B = you): agreement {r['agreement']:.0%}, "
              f"Cohen's kappa {r['kappa']:.2f}, weighted kappa {r['weighted kappa']:.2f}")
        print(r["table"].to_string())
        return
    llm = judge.llm_judgments()
    llm = llm[llm["human_grade"] >= 0]
    r = judge.agreement(llm["human_grade"], llm["llm_grade"])
    print(f"Recorded model labels and the WANDS judges on {r['pairs']} results (A = WANDS, B = model): "
          f"agreement {r['agreement']:.0%}, Cohen's kappa {r['kappa']:.2f}, weighted kappa {r['weighted kappa']:.2f}")
    print(r["table"].to_string())
