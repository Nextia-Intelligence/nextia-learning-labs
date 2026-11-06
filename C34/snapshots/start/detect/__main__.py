"""The command line of the detection job (start: learn normal, and score a day).

    python -m detect train --until 2025-09-30          learn normal from the 60 days up to that day
    python -m detect score --day 2025-10-01            the day's most unusual payments
"""
import argparse
import sys

from . import data
from . import model as model_mod
from .config import Settings
from .score import score_day


def cmd_train(s, args):
    p = data.payments(s.data_dir)
    m = model_mod.train(p, args.until, args.days, s.history_days, budget=s.budget)
    model_mod.save(m, s.state_dir)
    print(f"Trained {m.version} on {m.rows:,} payments ({m.first_day} to {m.last_day}). "
          f"Saved to {s.state_dir}/model.pkl.")


def cmd_score(s, args):
    p = data.payments(s.data_dir)
    m = model_mod.load(s.state_dir)
    sc = score_day(p, args.day, m, s.history_days)
    cols = ["payment_id", "ts", "customer_id", "amount", "country", "score"]
    print(f"{len(sc):,} payments on {args.day}. The {args.top} most unusual:")
    print(sc[cols].head(args.top).to_string(index=False))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m detect", description="Larkfield's payment detection job.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train", help="learn normal from a window of days")
    t.add_argument("--until", required=True, help="the last training day, YYYY-MM-DD")
    t.add_argument("--days", type=int, default=60, help="how many days (60)")
    sc = sub.add_parser("score", help="show the day's most unusual payments")
    sc.add_argument("--day", required=True)
    sc.add_argument("--top", type=int, default=5)
    args = ap.parse_args(argv)
    s = Settings()
    {"train": cmd_train, "score": cmd_score}[args.cmd](s, args)


if __name__ == "__main__":
    sys.exit(main())
