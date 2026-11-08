"""xp log: the team's test log (Mateo's). One line per finished test; `xp log stats` shows the habits."""

import csv
from datetime import date
from pathlib import Path

from ..runs import load_run

NAME = "log"
HELP = "add a finished test to the test log (xp log add RUN --decision ...), list it, or show its stats"
FILE = Path("test-log.csv")
COLUMNS = ["logged", "run", "about", "plan", "metric", "difference", "low", "high", "decision"]


def add(p):
    p.add_argument("action", choices=["add", "list", "stats"])
    p.add_argument("run", nargs="?")
    p.add_argument("--decision", help="ship, keep, no clear effect, do not use")
    p.add_argument("--plan", default="", help="the test plan file written before the test")


def run(args):
    if args.action == "add":
        if not args.decision:
            raise SystemExit("Give the decision: --decision ship|keep|'no clear effect'|'do not use'")
        run_ = load_run(args.run)
        a = run_.analysis()
        new = not FILE.exists()
        with FILE.open("a", newline="") as f:
            w = csv.DictWriter(f, COLUMNS)
            if new:
                w.writeheader()
            w.writerow({"logged": date.today().isoformat(), "run": run_.folder.name, "about": run_.meta["about"],
                        "plan": args.plan, "metric": a.get("metric", ""), "difference": a.get("difference", ""),
                        "low": a.get("low", ""), "high": a.get("high", ""), "decision": args.decision})
        print(f"Logged {run_.folder.name}: {args.decision}." + ("" if args.plan else " Warning: no test plan."))
        return
    if not FILE.exists():
        print("The test log is empty. Add a test with: xp log add RUN --decision ...")
        return
    rows = list(csv.DictReader(FILE.open()))
    if args.action == "list":
        def num(x):
            return f"{float(x):+.4f}" if x not in ("", None) else "?"
        for r in rows:
            print(f"{r['logged']}  {r['run']:<18} {r['decision']:<16} {r['metric']}: {num(r['difference'])} "
                  f"({num(r['low'])} to {num(r['high'])}) plan: {r['plan'] or 'NONE'}")
        return
    n = len(rows)
    ship = sum(r["decision"] == "ship" for r in rows)
    no_plan = sum(not r["plan"] for r in rows)
    print(f"{n} tests: {ship} shipped ({ship / n:.0%}), {no_plan} without a written plan.")
    print("Most changes do not win: a team that ships most of its tests may be shipping noise.")
