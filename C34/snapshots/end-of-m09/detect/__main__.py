"""The command line of the detection job.

    python -m detect train --until 2025-09-30          learn normal from the 60 days up to that day
    python -m detect score --day 2025-10-01            the day's most unusual payments (nothing is sent)
    python -m detect run --day 2025-10-01              score, group, keep the budget, send the new alerts
    python -m detect replay --from 2025-10-01 --to 2025-10-31
    python -m detect drift --day 2025-10-31            has normal moved since the training days?
    python -m detect review ALERT_ID real|not          a reviewer's answer
    python -m detect report --week-ending 2025-10-31   the weekly alert report
"""
import argparse
import json
import sys

import pandas as pd

from . import alerts as alerts_mod
from . import data, drift, ledger, report, suppress
from . import model as model_mod
from .config import Settings
from .score import score_day


def _days(a, b):
    return [d.date() for d in pd.date_range(a, b, freq="D")]


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


def run_day(s, p, m, day, quiet=False, features_frame=None):
    sc = score_day(p, day, m, s.history_days, features_frame)
    found = alerts_mod.group(sc, m, day)
    keep, held = suppress.apply(found, suppress.snoozed_customers(s.state_dir, day, s.snooze_days))
    chosen = alerts_mod.choose(keep, s.policy, s.budget, m.fixed_threshold)
    new, already = ledger.send(chosen, day, s.state_dir, s.alerts_dir)
    if held:
        s.state_dir.mkdir(parents=True, exist_ok=True)
        done = {json.loads(x)["alert_id"] for x in (s.state_dir / "snoozed.jsonl").read_text().splitlines()} \
            if (s.state_dir / "snoozed.jsonl").exists() else set()
        with open(s.state_dir / "snoozed.jsonl", "a") as f:
            for a in held:
                if a["alert_id"] not in done:
                    f.write(json.dumps({"alert_id": a["alert_id"], "day": str(day), "key": a["key"]}) + "\n")
    pressure = alerts_mod.above_threshold(sc, m.fixed_threshold)
    if not quiet:
        print(f"{day}: {len(sc):,} payments, {pressure} customers above the training threshold, "
              f"{len(found)} alert groups, {len(held)} snoozed. "
              f"Sent {len(new)} new alerts to {s.alerts_dir}/{day}.jsonl; {already} already sent.")
    return {"day": str(day), "payments": len(sc), "above_threshold": pressure, "groups": len(found),
            "snoozed": len(held), "sent": len(new), "already_sent": already}


def cmd_run(s, args):
    p = data.payments(s.data_dir)
    run_day(s, p, model_mod.load(s.state_dir), pd.Timestamp(args.day).date())


def cmd_replay(s, args):
    p = data.payments(s.data_dir)
    m = model_mod.load(s.state_dir)
    # the features of the whole period at once (faster); each day still sees at least 60 days of history
    ff = model_mod.behaviour_with_history(p, args.start, args.end, s.history_days)
    rows = [run_day(s, p, m, d, quiet=True, features_frame=ff) for d in _days(args.start, args.end)]
    t = pd.DataFrame(rows)
    print(t.to_string(index=False))
    print(f"Sent {t.sent.sum()} alerts in {len(t)} days ({t.sent.mean():.1f} a day, budget {s.budget}, "
          f"policy {s.policy}).")


def cmd_drift(s, args):
    p = data.payments(s.data_dir)
    m = model_mod.load(s.state_dir)
    table, pressure = drift.check(p, m, args.day, args.days, s.budget, s.history_days)
    print(f"Model {m.version}. PSI of the last {args.days} days against the training days:")
    print(table.to_string(index=False))
    print("Customers above the training threshold per day: " + ", ".join(str(int(v)) for v in pressure))
    print(drift.verdict(table, pressure, s.budget))


def cmd_review(s, args):
    rec = suppress.add_review(s.state_dir, s.alerts_dir, args.alert_id, args.label)
    print(f"Saved: alert {rec['alert_id']} of {rec['day']} is {rec['label']}.")


def cmd_report(s, args):
    print(report.weekly(s.state_dir, s.alerts_dir, args.week_ending))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m detect", description="Larkfield's payment detection job.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("train", help="learn normal from a window of days")
    t.add_argument("--until", required=True, help="the last training day, YYYY-MM-DD")
    t.add_argument("--days", type=int, default=60, help="how many days (60)")
    sc = sub.add_parser("score", help="show the day's most unusual payments")
    sc.add_argument("--day", required=True)
    sc.add_argument("--top", type=int, default=5)
    r = sub.add_parser("run", help="send the day's alerts")
    r.add_argument("--day", required=True)
    rp = sub.add_parser("replay", help="run every day of a period")
    rp.add_argument("--from", dest="start", required=True)
    rp.add_argument("--to", dest="end", required=True)
    d = sub.add_parser("drift", help="has normal moved?")
    d.add_argument("--day", required=True)
    d.add_argument("--days", type=int, default=7)
    rv = sub.add_parser("review", help="save a reviewer's answer")
    rv.add_argument("alert_id")
    rv.add_argument("label", choices=["real", "not"])
    rep = sub.add_parser("report", help="the weekly alert report")
    rep.add_argument("--week-ending", required=True)
    args = ap.parse_args(argv)
    s = Settings()
    {"train": cmd_train, "score": cmd_score, "run": cmd_run, "replay": cmd_replay, "drift": cmd_drift,
     "review": cmd_review, "report": cmd_report}[args.cmd](s, args)


if __name__ == "__main__":
    sys.exit(main())
