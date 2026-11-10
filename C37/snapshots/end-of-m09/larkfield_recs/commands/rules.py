"""recs rules: what each business rule changes, one rule at a time."""

from .. import beyond, data, metrics, registry
from .. import rules as rules_mod

NAME = "rules"
HELP = "Measure each business rule alone, then all together, on one method's lists (test period)."

def add(p):
    p.add_argument("method", help="the method whose lists the rules change, for example two-stage")
    p.add_argument("--period", default="test", choices=["test", "validation"])
    p.add_argument("--quick", action="store_true", help="a fixed sample of 1,000 customers")
    p.add_argument("--set", action="append", metavar="NAME=VALUE", help="change a rule, for example min_margin=0.12")

def run(args):
    shop = data.load()
    p = data.Period(shop, args.period, quick=args.quick)
    m = registry.make(args.method, p).fit()
    long = m.recommend(p.users, 50)
    base_rules = {**rules_mod.load(), **registry.parse_settings(args.set)}
    off = {key: (False if isinstance(v, bool) else (0 if key == "min_margin" else None)) for key, v in base_rules.items()}
    rows = [("no rules", long[:, :10])]
    for key, value in base_rules.items():
        if value in (False, 0, 0.0, None):
            continue
        one = dict(off)
        one[key] = value
        rows.append((f"only {key} = {value}", rules_mod.apply(long, p, one)))
    rows.append(("all rules", rules_mod.apply(long, p, base_rules)))
    pr = shop.products
    sens, age = pr.sensitive.to_numpy(dtype=bool), pr.age_restricted.to_numpy(dtype=bool)
    oos = ~pr.in_stock.to_numpy(dtype=bool)
    print(f"{args.method}, {args.period} period, {len(p.users):,} customers")
    print(f"{'lists':<34}{'recall@10':>10}{'NDCG@10':>9}{'coverage':>9}{'diversity':>10}"
          f"{'changed':>9}{'out of stock':>13}{'sensitive':>10}{'alcohol':>8}")
    base = rows[0][1]
    for name, recs in rows:
        per = metrics.per_customer(recs, p.truth, 10)
        b = beyond.measures(recs, p)
        changed = float((recs != base).any(axis=1).mean())
        shown = recs[recs >= 0]
        print(f"{name:<34}{per['recall'].mean():>10.3f}{per['ndcg'].mean():>9.3f}"
              f"{metrics.coverage(recs, p.available):>9.1%}{b['diversity']:>10.2f}{changed:>9.0%}"
              f"{oos[shown].mean():>13.1%}{sens[shown].mean():>10.1%}{age[shown].mean():>8.1%}")
