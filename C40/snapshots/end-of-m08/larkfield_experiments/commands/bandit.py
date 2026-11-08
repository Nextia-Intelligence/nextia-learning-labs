"""xp bandit: Thompson sampling against a fixed equal split, for four email subject lines (simulated clicks)."""

import numpy as np

from ..bandit import prob_best, run_bandit
from ..stats import diff_means

NAME = "bandit"
HELP = "Thompson sampling against a fixed split for subject lines with known click rates (--repeats for averages)"
DEFAULT_RATES = "0.040,0.046,0.052,0.044"


def add(p):
    p.add_argument("--rates", default=DEFAULT_RATES, help=f"the true click rates (default: {DEFAULT_RATES})")
    p.add_argument("--visitors", type=int, default=40_000)
    p.add_argument("--seed", type=int, default=40)
    p.add_argument("--repeats", type=int, default=0, help="repeat both N times and report averages")


def run(args):
    rates = np.array([float(x) for x in args.rates.split(",")])
    names = [chr(65 + i) for i in range(len(rates))]
    best = rates.argmax()
    rng = np.random.default_rng(args.seed)
    print(f"Subject lines {', '.join(f'{n} {r:.1%}' for n, r in zip(names, rates))} (true click rates, simulated); "
          f"{args.visitors:,} emails.")
    for policy, label in (("fixed", "fixed equal split (A/B/n test)"), ("thompson", "Thompson sampling")):
        shown, clicks, shares = run_bandit(rates, args.visitors, rng, policy)
        lost = rates.max() * args.visitors - (shown * rates).sum()
        print(f"  {label}: {int(clicks.sum()):,} clicks; expected clicks lost against always the best: {lost:,.0f}")
        print(f"    traffic share by tenth of the emails, best line {names[best]}: "
              + " ".join(f"{s[best]:.0%}" for s in shares))
        pb = prob_best(shown, clicks, rng)
        print("    chance each line is best: " + ", ".join(f"{n} {p:.2f}" for n, p in zip(names, pb)))
        rest = [i for i in range(len(rates)) if i != best]
        worst = rest[int(np.argmin(rates[rest]))]
        n_b, n_w = int(shown[best]), int(shown[worst])
        r = diff_means(np.r_[np.ones(int(clicks[worst])), np.zeros(n_w - int(clicks[worst]))],
                       np.r_[np.ones(int(clicks[best])), np.zeros(n_b - int(clicks[best]))])
        print(f"    {names[best]} − {names[worst]}: {r['difference']:+.4f} (95% interval {r['low']:+.4f} to "
              f"{r['high']:+.4f}; true {rates[best] - rates[worst]:+.4f}); emails: {n_b:,} and {n_w:,}")
    if args.repeats:
        res = {"fixed": [], "thompson": []}
        for i in range(args.repeats):
            for policy in res:
                shown, clicks, _ = run_bandit(rates, args.visitors, np.random.default_rng(10_000 + i), policy)
                res[policy].append((rates.max() * args.visitors - (shown * rates).sum(),
                                    int(np.argmax(clicks / np.maximum(shown, 1)) == best)))
        for policy, v in res.items():
            v = np.array(v)
            print(f"  {args.repeats} repeats, {policy}: clicks lost {v[:, 0].mean():,.0f} on average; the best line "
                  f"has the highest observed rate in {v[:, 1].mean():.0%} of them")
