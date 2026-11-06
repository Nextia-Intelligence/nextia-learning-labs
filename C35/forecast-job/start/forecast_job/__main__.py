"""The command line of the forecasting job (the start of Module 8: one week, one folder).

    python -m forecast_job run --week 2025-03-10            plan one week (Monday): checks, forecast, order, roster

Options: --data (default data), --out (default plan).
"""

import argparse
import sys
from pathlib import Path

from . import model, plan
from .data import DataError, check, load, monday


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m forecast_job", description="Larkfield's weekly forecasting job.")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("run")
    p.add_argument("--week", required=True)
    p.add_argument("--data", default="data")
    p.add_argument("--out", default="plan")
    a = ap.parse_args(argv)

    week = monday(a.week)
    inputs = load(a.data, week)
    try:
        warnings = check(inputs)
    except DataError as e:
        print(f"Week {week.date()}: STOPPED, the data is not safe to use: {e}. Nothing was written.")
        raise SystemExit(2) from None
    fc = model.forecast_products(inputs)
    totals = model.reconcile(fc, inputs.products)
    orders = plan.stock_orders(fc, inputs.products)
    rost = plan.roster(model.forecast_tickets(inputs))
    out = Path(a.out) / str(week.date())
    plan.write(out, fc, totals, orders, rost)
    s = plan.summary(orders, rost)
    print(f"Week {week.date()}: {s['order_units']} units to order (expected cost {s['order_expected_cost_usd']} "
          f"dollars), {s['agent_hours']} agent hours (expected cost {s['roster_expected_cost_usd']} dollars), "
          f"{len(warnings)} warnings. Plan: {out}")
    for w in warnings:
        print(f"  warning: {w}")


if __name__ == "__main__":
    sys.exit(main())
