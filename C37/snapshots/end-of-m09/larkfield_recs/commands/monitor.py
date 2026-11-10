"""recs monitor: weekly health of a recommender over the last weeks of the log, and a stale model beside it."""

import numpy as np

from .. import beyond, data, metrics, registry, segments

NAME = "monitor"
HELP = "Week by week: recall by segment, coverage, short lists and new products, for a model retrained weekly and one never retrained."


def add(p):
    p.add_argument("--method", default="als")
    p.add_argument("--weeks", type=int, default=8)


def run(args):
    shop = data.load()
    last = int(shop.events.day.max())
    first_week = last - 7 * args.weeks + 1
    stale = registry.make(args.method, data.Period(shop, "w", start_day=first_week, end_day=first_week + 6)).fit()
    print(f"{args.method}: retrained every week; 'stale model' = the model of the first week, never retrained")
    print(f"{'week from':<12}{'customers':>10}{'recall new':>11}{'occasional':>11}{'loyal':>7}{'coverage':>9}"
          f"{'new prod.':>10}{'short lists':>12}{'stale model':>12}")
    for w in range(args.weeks):
        s = first_week + 7 * w
        p = data.Period(shop, "w", start_day=s, end_day=min(s + 6, last))
        m = registry.make(args.method, p).fit()
        recs = m.recommend(p.users, 10)
        per = metrics.per_customer(recs, p.truth, 10)
        seg = segments.by_segment(per, p)
        b = beyond.measures(recs, p)
        stale.period = p        # same model, this week's customers and products on sale
        old = stale.recommend(p.users, 10)
        old_recall = metrics.per_customer(old, p.truth, 10)["recall"].mean()
        short = float((recs < 0).any(axis=1).mean())
        print(f"{p.cutoff!s:<12}{len(p.users):>10,}{seg.get('new', {}).get('recall', np.nan):>11.3f}"
              f"{seg.get('occasional', {}).get('recall', np.nan):>11.3f}{seg.get('loyal', {}).get('recall', np.nan):>7.3f}"
              f"{metrics.coverage(recs, p.available):>9.1%}{b['new_share']:>10.1%}{short:>12.1%}{old_recall:>12.3f}")
