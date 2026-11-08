"""recs online: read the simulated A/B test of three models, with the main measure and the guardrails."""

import numpy as np
import pandas as pd

from .. import metrics
from ..paths import data_dir

NAME = "online"
HELP = "Read the simulated A/B test (data/online/ab_test.csv): added revenue per visit and the guardrails, per model."


def add(p):
    p.add_argument("--baseline", default="trending", help="the model the others are compared with (default trending)")


def run(args):
    df = pd.read_csv(data_dir() / "online" / "ab_test.csv")
    print("SIMULATED A/B test on the course's behaviour model (not real customers): "
          f"{len(df):,} customers, each shown one model's lists for two weeks")
    print(f"{'model':<11}{'customers':>10}{'visits':>8}{'clicks/visit':>13}{'from suggestions':>17}{'added':>8}"
          f"{'  95% interval':<17}{'returns':>8}{'unsubscribed':>13}   (dollars per visit)")
    for arm, d in df.groupby("arm", sort=False):
        v = d.visits.sum()
        mv = d.visits.mean()
        _, lo, hi = metrics.bootstrap((d.added_revenue / mv).to_numpy())
        print(f"{arm:<11}{len(d):>10,}{v:>8,}{d.clicks.sum() / v:>13.3f}{d.revenue_from_suggestions.sum() / v:>17.2f}"
              f"{d.added_revenue.sum() / v:>8.2f}  {lo:5.2f} to {hi:5.2f}  "
              f"{d.returns.sum() / max(d.orders.sum(), 1):>8.1%}{d.unsubscribed.sum() / max((d.emails > 0).sum(), 1):>13.2%}")
    base = df[df.arm == args.baseline]
    print(f"Difference in added revenue per visit against {args.baseline} (95% interval, customers resampled):")
    for arm, d in df.groupby("arm", sort=False):
        if arm == args.baseline:
            continue
        diffs = []
        rng = np.random.default_rng(37)
        a, b = base.added_revenue.to_numpy(), d.added_revenue.to_numpy()
        av, bv = base.visits.to_numpy(), d.visits.to_numpy()
        for _ in range(1000):
            i, j = rng.integers(0, len(a), len(a)), rng.integers(0, len(b), len(b))
            diffs.append(b[j].sum() / bv[j].sum() - a[i].sum() / av[i].sum())
        point = b.sum() / bv.sum() - a.sum() / av.sum()
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        verdict = "clear" if lo > 0 or hi < 0 else "not clear (the interval includes 0)"
        print(f"  {arm:<11}{point:+.2f} dollars ({lo:+.2f} to {hi:+.2f}): {verdict}")
