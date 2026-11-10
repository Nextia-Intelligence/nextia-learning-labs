"""The evaluation harness: one method, one period, every measure, saved for `recs compare`.

The same customers, the same period and the same measures for every method: that is what makes the comparison
table fair.
"""

import json
import time

import numpy as np

from . import beyond, data, metrics, registry, segments
from .paths import outputs_dir

RANKING = ("precision", "recall", "hit", "map", "ndcg")


def run(method, period="test", k=10, quick=False, settings=None, rules=None, shop=None, period_obj=None):
    shop = shop or data.load()
    p = period_obj or data.Period(shop, period, quick=quick)
    m = registry.make(method, p, settings)
    t0 = time.perf_counter()
    m.fit()
    t1 = time.perf_counter()
    if rules:
        from . import rules as rules_mod
        recs = rules_mod.apply(m.recommend(p.users, k * 5), p, rules, k)
    else:
        recs = m.recommend(p.users, k)
    t2 = time.perf_counter()
    per = metrics.per_customer(recs, p.truth, k, RANKING)
    res = {
        "method": method, "settings": settings or {}, "rules": sorted(rules) if rules else [],
        "period": p.name, "cutoff": str(p.cutoff), "quick": quick, "k": k, "customers": len(p.users),
        "fit_seconds": round(t1 - t0, 2), "recommend_seconds": round(t2 - t1, 2),
        "coverage": metrics.coverage(recs, p.available, k),
    }
    for name in RANKING:
        res[name] = float(per[name].mean())
    res["recall_ci"] = metrics.bootstrap(per["recall"])[1:]
    res["ndcg_ci"] = metrics.bootstrap(per["ndcg"])[1:]
    res.update(beyond.measures(recs, p, k))
    res["segments"] = segments.by_segment(per, p)
    res["new_products"] = segments.new_product_recall(recs, p, k)
    save(res, per, p)
    return res, recs, p


def run_name(res):
    s = res["method"]
    if res["settings"]:
        s += "[" + ",".join(f"{k}={v}" for k, v in sorted(res["settings"].items())) + "]"
    if res["rules"]:
        s += "+rules"
    return f"{s}-{res['period']}{'-quick' if res['quick'] else ''}"


def save(res, per, p):
    d = outputs_dir() / "runs"
    d.mkdir(parents=True, exist_ok=True)
    name = run_name(res)
    (d / f"{name}.json").write_text(json.dumps(res, indent=2) + "\n")
    np.savez(d / f"{name}.npz", users=p.users, segment=p.segment, **per)


def load_run(name, period="test", quick=False):
    d = outputs_dir() / "runs"
    base = name if name.endswith(("-test", "-validation", "-launch", "-random", "-quick")) else \
        f"{name}-{period}{'-quick' if quick else ''}"
    f = d / f"{base}.json"
    if not f.exists():
        raise SystemExit(f"No saved run {base}. Run first: {evaluate_command(name, period, quick)}")
    return json.loads(f.read_text()), dict(np.load(d / f"{base}.npz"))


def evaluate_command(name, period="test", quick=False):
    """The `recs evaluate` command that saves the run `name` (for example als+new[slots=1]+rules)."""
    rules = name.endswith("+rules")
    name = name.removesuffix("+rules")
    method, _, settings = name.partition("[")
    cmd = f"recs evaluate {method}"
    for pair in filter(None, settings.rstrip("]").split(",")):
        cmd += f" --set {pair}"
    if rules:
        cmd += " --rules"
    if period != "test":
        cmd += f" --period {period}"
    return cmd + (" --quick" if quick else "")


def describe(method):
    return registry.all_methods()[method][2]


def report(res, by=None):
    period = {"test": "test period", "validation": "validation period", "launch": "launch period (new range)",
              "random": "random split (leaky)"}[res["period"]]
    print(f"Method {res['method']} ({describe(res['method'])}), {period}"
          + (f", settings {res['settings']}" if res["settings"] else "")
          + (f", rules: {', '.join(res['rules'])}" if res["rules"] else ""))
    print(f"Customers scored: {res['customers']:,}{' (quick sample)' if res['quick'] else ''}; "
          + ("trained on every event except the held-out orders" if res["period"] == "random"
             else f"trained on events before {res['cutoff']}"))
    lo, hi = res["recall_ci"]
    print(f"recall@{res['k']} {res['recall']:.3f} (95% interval {lo:.3f} to {hi:.3f}), "
          f"NDCG@{res['k']} {res['ndcg']:.3f}, MAP@{res['k']} {res['map']:.3f}, "
          f"precision@{res['k']} {res['precision']:.3f}, hit rate {res['hit']:.1%}")
    print(f"coverage {res['coverage']:.1%} of the products on sale, novelty {res['novelty']:.2f} bits, "
          f"diversity {res['diversity']:.2f}, new products in the lists {res['new_share']:.1%}")
    print(f"time: fit {res['fit_seconds']:.1f} s, suggestions {res['recommend_seconds']:.1f} s")
    if by == "segment":
        print(f"{'segment':<12}{'customers':>10}{'recall@10':>11}{'NDCG@10':>9}  95% interval (recall)")
        for seg, v in res["segments"].items():
            print(f"{seg:<12}{v['customers']:>10,}{v['recall']:>11.3f}{v['ndcg']:>9.3f}  "
                  f"{v['recall_ci'][0]:.3f} to {v['recall_ci'][1]:.3f}")
        npr = res["new_products"]
        print(f"new products: {npr['orders']:,} orders of new products in the period; "
              f"recall@10 on them {npr['recall']:.3f}")
