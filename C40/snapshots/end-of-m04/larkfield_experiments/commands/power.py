"""xp power: how many customers and days a test needs, by formula and (with --simulate) by simulation."""

import math

from ..power import power_of, sample_size, simulated_power
from ..runs import load_run

NAME = "power"
HELP = "sample size, power and duration of a test (formula with statsmodels; --simulate checks it)"


def add(p):
    p.add_argument("--baseline", type=float, help="the control mean, e.g. 0.09 for a 9%% order rate")
    p.add_argument("--mde", type=float, required=True,
                   help="the smallest effect worth finding, e.g. 0.01 (one percentage point)")
    p.add_argument("--sd", type=float, help="the standard deviation of a mean metric (leave out for a proportion)")
    p.add_argument("--from-run", dest="from_run", help="take the baseline and sd of --metric from this run's group A")
    p.add_argument("--metric", default="revenue")
    p.add_argument("--power", type=float, default=0.8)
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--per-day", type=int, dest="per_day", help="new customers who enter the test each day")
    p.add_argument("--simulate", type=int, metavar="RUNS",
                   help="check by simulation: RUNS fake tests of the computed size with the effect --mde (customers "
                        "drawn from --from-run's group A, or 0/1 values at the baseline)")


def run(args):
    baseline, sd = args.baseline, args.sd
    if args.from_run:
        df = load_run(args.from_run).table("customers")
        a = df[df["variant"] == "A"][args.metric]
        baseline, sd = float(a.mean()), float(a.std())
        print(f"From {args.from_run}, group A: {args.metric} mean {baseline:.4f}, standard deviation {sd:.4f}.")
    if baseline is None:
        raise SystemExit("Give --baseline (and --sd for a mean metric), or --from-run.")
    n = sample_size(baseline, args.mde, sd, args.power, args.alpha)
    kind = "a proportion" if sd is None else f"a mean with standard deviation {sd:.3f}"
    print(f"To find an effect of {args.mde:+g} on {kind} (baseline {baseline:g}) with {args.power:.0%} power at "
          f"alpha {args.alpha:g}:")
    print(f"  {n:,} customers per group, {2 * n:,} in total.")
    for share in (0.5, 0.75, 1.0, 1.5, 2.0):
        print(f"  with {round(n * share):,} per group, power = {power_of(round(n * share), baseline, args.mde, sd, args.alpha):.2f}")
    if args.per_day:
        days = math.ceil(2 * n / args.per_day)
        weeks = math.ceil(days / 7)
        print(f"  At {args.per_day:,} new customers a day: {days} days; run full weeks: {weeks} "
              f"week{'s' if weeks > 1 else ''} ({7 * weeks} days).")
    if args.simulate:
        import numpy as np

        from ..stats import diff_means
        values = a.to_numpy() if args.from_run else None

        def one(seed):
            rng = np.random.default_rng(seed)
            if values is None:
                ya, yb = rng.random(n) < baseline, rng.random(n) < baseline + args.mde
            else:
                ya, yb = rng.choice(values, n), rng.choice(values, n) + args.mde
            return diff_means(ya, yb)["p"]
        sp = simulated_power(one, args.simulate)
        print(f"  Simulated: {args.simulate} fake tests with {n:,} customers per group and a true effect of "
              f"{args.mde:+g}: {sp:.0%} found it (p < {args.alpha:g}).")
