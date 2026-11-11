"""`vision zones`: pass, check and fail lines from recorded anomaly scores and Hamid's daily budget."""
import json
from pathlib import Path

from larkvision import data as D
from larkvision.commands.compare import add_row
from larkvision.compare import choose_lines, inspection_costs, inspection_row, roc_auc
from larkvision.paths import data_dir


def register(sub):
    p = sub.add_parser("zones", help="pass/check/fail lines from the review budget")
    p.add_argument("--method", default="small_patchcore", help="recorded scores: predictions/returns_<method>.json")
    p.add_argument("--budget", type=int, default=None, help="checks a day (default: the cost table's)")
    p.add_argument("--list", action="store_true", help="list the recorded methods")
    p.set_defaults(run=run)


def run(args):
    d = data_dir(args.data)
    if args.list:
        for f in sorted((Path(d) / "predictions").glob("returns_*.json")):
            print(f.stem.removeprefix("returns_"))
        return
    scores = json.loads((Path(d) / f"predictions/returns_{args.method}.json").read_text())
    costs = D.costs(d)
    if args.budget is not None:
        costs = dict(costs, checks_per_day=args.budget)
    val, test = D.returns(d, "val"), D.returns(d, "test")
    sv = [scores[r["item_id"]] for r in val]
    dv = [r["status"] == "damaged" for r in val]
    lines = choose_lines(sv, dv, costs)
    st = [scores[r["item_id"]] for r in test]
    dt = [r["status"] == "damaged" for r in test]
    c = inspection_costs(st, dt, lines["check_line"], lines["fail_line"], costs)
    print(f"{args.method}: lines chosen on the validation photos for {costs['checks_per_day']} checks a day: "
          f"check from {lines['check_line']:.4g}, fail from {lines['fail_line']:.4g}")
    print(f"Test ({c['items']} photos, {c['damaged']} damaged; AUROC {roc_auc(st, dt):.3f}), per day at "
          f"{costs['returns_per_day']} returns: {c['checks_per_day']:.0f} checks, "
          f"{c['damaged_sold_as_new_per_day']:.1f} damaged sold as new, "
          f"{c['good_marked_damaged_per_day']:.1f} good items lost; cost {c['cost_per_day']:.0f}"
          " dollars a day")
    row = inspection_row(args.method, sv, dv, st, dt, [r["damage"] for r in test], "returns test", None, None, None,
                         "-")
    if costs["checks_per_day"] != D.costs(d)["checks_per_day"]:
        # inspection_row uses the cost table's budget: keep this run's lines and cost, and say the budget.
        row = dict(row, setting=f"returns test, {costs['checks_per_day']} checks a day", value=c["cost_per_day"],
                   lines=[lines["check_line"], lines["fail_line"]], test=c, worst="-", worst_value=None)
    add_row(row)
