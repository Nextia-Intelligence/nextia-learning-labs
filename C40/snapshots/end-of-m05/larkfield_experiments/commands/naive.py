"""xp naive: the answers to distrust. Before against after (launch), users against non-users (logs)."""

from ..runs import load_run

NAME = "naive"
HELP = "the naive answer of a run without a test: before against after, or users against non-users"


def add(p):
    p.add_argument("run", nargs="?", help="a run folder or scenario name (default: the last run)")
    p.add_argument("--weeks", type=int, default=4, help="weeks before and after the launch (launch only)")


def run(args):
    run_ = load_run(args.run)
    if run_.name == "launch":
        d = run_.table("daily")
        launch = run_.meta["events"]["launch"]
        import pandas as pd
        day = pd.Timestamp(launch)
        dates = pd.to_datetime(d["date"])
        have = ((dates.max() - day).days + 1) // 7
        if not 1 <= args.weeks <= have:
            raise SystemExit(f"--weeks {args.weeks}: the run {run_.folder.name} has {have} full weeks after the launch. "
                             f"Use 1 to {have}.")
        before = d[(dates >= day - pd.Timedelta(weeks=args.weeks)) & (dates < day)]
        after = d[(dates >= day) & (dates < day + pd.Timedelta(weeks=args.weeks))]
        sb, sa = before["sales"].sum(), after["sales"].sum()
        span = f"{args.weeks} week{'s' if args.weeks != 1 else ''}"
        print(f"Sales in the {span} before the launch ({before.date.min()} to {before.date.max()}): "
              f"{sb:,.0f} dollars")
        print(f"Sales in the {span} after the launch ({after.date.min()} to {after.date.max()}): "
              f"{sa:,.0f} dollars")
        print(f"Change: {sa / sb - 1:+.1%}. The same weeks had: Thanksgiving, an autumn sale.")
        result = {"command": NAME, "kind": "before_after", "weeks": args.weeks, "change": sa / sb - 1,
                  "difference": sa - sb}
    elif run_.name in ("logs",):
        d = run_.table("customers")
        users, others = d[d["used_block"] == 1], d[d["used_block"] == 0]
        mu, mo = users["revenue"].mean(), others["revenue"].mean()
        print(f"Customers who used the block: {len(users):,}, mean revenue {mu:.2f} dollars")
        print(f"Customers who did not:        {len(others):,}, mean revenue {mo:.2f} dollars")
        print(f"Difference: {mu - mo:+.2f} dollars ({mu / mo - 1:+.1%}).")
        result = {"command": NAME, "kind": "users", "difference": mu - mo, "change": mu / mo - 1}
    else:
        raise SystemExit("xp naive works on the runs without a test: launch, logs. "
                         "For a randomised test, use: xp analyse")
    path = run_.save_analysis(result)
    print(f"Saved to {path}. Compare with the true effect: xp check")


def check(analysis, truth):
    if analysis["kind"] == "before_after":
        t = truth["true_effect_after"]
        return [f"Naive answer: sales {analysis['change']:+.1%} after the launch.",
                f"True effect of the block (from the simulator): {t['relative']:+.1%} of sales "
                f"({t['sales']:,.0f} dollars in the 4 weeks after the launch).",
                f"The naive answer is {100 * (analysis['change'] - t['relative']):.1f} percentage points too high: the holiday, "
                f"the sale and the trend are in it too."] + (
                [f"Your naive answer used {analysis['weeks']} week{'s' if analysis['weeks'] != 1 else ''} on each side; "
                 "the true effect is for the 4 weeks after the launch."] if analysis.get("weeks", 4) != 4 else [])
    t = truth["att"]["effect"]
    return [f"Naive answer: users spent {analysis['difference']:+.2f} dollars more ({analysis['change']:+.1%}).",
            f"True effect of the block on its users (from the simulator): {t:+.2f} dollars per customer.",
            f"The naive answer is {analysis['difference'] / t:.1f} times the true effect: the users were "
            f"different customers before they used the block."]
