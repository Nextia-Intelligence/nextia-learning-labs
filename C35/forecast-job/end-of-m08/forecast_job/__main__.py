"""The command line of the forecasting job.

    python -m forecast_job run --week 2025-03-10            plan one week (Monday): checks, forecast, order, roster
    python -m forecast_job replay --start 2025-03-03 --weeks 12
                                                            plan week after week, and check each finished week
    python -m forecast_job check --week 2025-03-10          compare a plan's first week with the sales
    python -m forecast_job fva                              did the planners' overrides help?
    python -m forecast_job note --week 2025-03-10           the numbers for the manager's note, and the
                                                            check of the recorded draft

Options: --data (default data), --store (default runs), --overrides (default none; replay uses
planner/overrides_replay.csv), --force (replace a plan made with other inputs).
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from . import config, model, monitor, note, overrides, plan, store
from .data import DataError, check, load, monday

REPLAY_OVERRIDES = Path("planner/overrides_replay.csv")
RECORDED_NOTES = Path("planner/notes_recorded.json")


def run_week(week, data_dir, store_dir, overrides_path=None, force=False, quiet=False):
    """Plan one week. Returns the summary, or None when the data check stopped the run."""
    say = (lambda *a: None) if quiet else print
    inputs = load(data_dir, week)
    try:
        warnings = check(inputs)
    except DataError as e:
        print(f"Week {week.date()}: STOPPED, the data is not safe to use: {e}. Nothing was written.")
        return None
    ov = overrides.for_week(overrides.read(overrides_path), week)
    fp = store.fingerprint(inputs, ov)
    out = store.begin(store_dir, week, say, fp, force=force)
    if out is None:
        return json.loads((store.week_dir(store_dir, week) / "run.json").read_text())["summary"]
    fc = model.forecast_products(inputs)
    totals = model.reconcile(fc, inputs.products)
    orders = overrides.apply(plan.stock_orders(fc, inputs.products), ov)
    rost = plan.roster(model.forecast_tickets(inputs))
    plan.write(out, fc, totals, orders, rost)
    summary = plan.summary(orders, rost)
    summary["overrides"] = len(ov)
    end = week + pd.Timedelta(days=config.HORIZON_DAYS)
    for c in inputs.price_changes.itertuples():
        if week <= pd.Timestamp(c.date) < end:
            warnings.append(f"{c.product_id} changes price on {c.date.date()} (to {c.new_price}): "
                            "the forecast does not know the new price, so check its order")
    store.finish(out, week, fp, summary, warnings)
    say(f"Week {week.date()}: {summary['order_units']} units to order "
        f"(expected cost {summary['order_expected_cost_usd']} dollars), {summary['agent_hours']} agent hours "
        f"(expected cost {summary['roster_expected_cost_usd']} dollars), {len(warnings)} warnings, "
        f"{len(ov)} overrides. Plan: {out}")
    for w in warnings:
        say(f"  warning: {w}")
    return summary


def check_and_alarm(week, data_dir, store_dir, quiet=False):
    c = monitor.check_week(store_dir, data_dir, week)
    found = monitor.alarms(store_dir, week)
    meta_path = store.week_dir(store_dir, week) / "run.json"
    meta = json.loads(meta_path.read_text())
    meta["alarms"] = [monitor.describe(a) for a in found]
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    if not quiet:
        worst = c.loc[c["bias_pct"].abs().idxmax()]
        total = 100 * (c["forecast"].sum() - c["sales"].sum()) / c["sales"].sum()
        print(f"Check {week.date()}: all categories {total:+.1f}%, largest {worst['category']} "
              f"{worst['bias_pct']:+.1f}%, {len(found)} alarms")
        for a in found:
            print("  " + monitor.describe(a))
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m forecast_job", description="Larkfield's weekly forecasting job.")
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("run", "replay", "check", "fva", "note"):
        p = sub.add_parser(name)
        p.add_argument("--data", default="data")
        p.add_argument("--store", default="runs")
        if name in ("run", "check", "note"):
            p.add_argument("--week", required=True)
        if name in ("run", "replay"):
            p.add_argument("--overrides", default=None)
            p.add_argument("--force", action="store_true")
        if name == "replay":
            p.add_argument("--start", required=True)
            p.add_argument("--weeks", type=int, default=12)
    a = ap.parse_args(argv)
    try:
        command(a)
    except store.AlreadyPlanned as e:
        print(e)
        raise SystemExit(2) from None


def command(a):
    if a.command == "run":
        if run_week(monday(a.week), a.data, a.store, a.overrides, a.force) is None:
            raise SystemExit(2)
    elif a.command == "replay":
        start = monday(a.start)
        ov = a.overrides or (REPLAY_OVERRIDES if REPLAY_OVERRIDES.exists() else None)
        alarms_seen, stopped = 0, 0
        for k in range(a.weeks):
            week = start + pd.Timedelta(weeks=k)
            if run_week(week, a.data, a.store, ov, a.force) is None:
                stopped += 1
                print("  The plan of the week before stays in use. Fix the feed, then run this week again.")
            last = week - pd.Timedelta(weeks=1)
            if k > 0 and (store.week_dir(a.store, last) / "run.json").exists():
                alarms_seen += len(check_and_alarm(last, a.data, a.store))
        print(f"Replayed {a.weeks} weeks from {start.date()}: {alarms_seen} bias alarms, {stopped} weeks stopped.")
    elif a.command == "check":
        check_and_alarm(monday(a.week), a.data, a.store)
    elif a.command == "fva":
        f = overrides.value_added(a.store, a.data)
        if f.empty:
            print("No overrides with 14 finished days yet.")
            return
        with pd.option_context("display.width", 160, "display.max_columns", 20):
            print(f.to_string(index=False))
        helped = int((f["fva_usd"] > 0).sum())
        print(f"{len(f)} overrides: {helped} helped, {len(f) - helped} did not. "
              f"Forecast value added: {f['fva_usd'].sum():+.0f} dollars in total.")
        print(f.groupby("reason")["fva_usd"].agg(["count", "sum"]).round(0).to_string())
    elif a.command == "note":
        week = monday(a.week)
        facts = note.numbers(a.store, week)
        print(json.dumps(facts, indent=2))
        rec = note.recorded(RECORDED_NOTES, week) if RECORDED_NOTES.exists() else None
        if rec is None:
            print("No recorded draft for this week.")
            return
        print(f"\nRecorded draft ({rec['model']}, {rec['input_tokens']} + {rec['output_tokens']} tokens):\n")
        print(rec["note"])
        bad = note.check_note(rec["note"], facts)
        print("\nCheck: every number is in the plan." if not bad else
              f"\nCheck: NOT SUPPORTED by the plan: {', '.join(bad)}. Fix these before you send the note.")


if __name__ == "__main__":
    sys.exit(main())
