"""The evaluation harness: one method, one period, the first measures (recall, NDCG, coverage), saved.

The same customers, the same period and the same measures for every method: that is what makes the comparison
table fair.
"""

import json
import time

import numpy as np

from . import data, metrics, registry
from .paths import outputs_dir

RANKING = ("precision", "recall", "hit", "map", "ndcg")


def run(method, period="test", k=10, quick=False, settings=None, shop=None, period_obj=None):
    shop = shop or data.load()
    p = period_obj or data.Period(shop, period, quick=quick)
    m = registry.make(method, p, settings)
    t0 = time.perf_counter()
    m.fit()
    t1 = time.perf_counter()
    recs = m.recommend(p.users, k)
    t2 = time.perf_counter()
    per = metrics.per_customer(recs, p.truth, k, RANKING)
    res = {
        "method": method, "settings": settings or {}, "rules": [],
        "period": p.name, "cutoff": str(p.cutoff), "quick": quick, "k": k, "customers": len(p.users),
        "fit_seconds": round(t1 - t0, 2), "recommend_seconds": round(t2 - t1, 2),
        "coverage": metrics.coverage(recs, p.available, k),
    }
    for name in RANKING:
        res[name] = float(per[name].mean())
    res["recall_ci"] = metrics.bootstrap(per["recall"])[1:]
    res["ndcg_ci"] = metrics.bootstrap(per["ndcg"])[1:]
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
        raise SystemExit(f"No saved run {base}. Run first: recs evaluate {name}" + (" --quick" if quick else ""))
    return json.loads(f.read_text()), dict(np.load(d / f"{base}.npz"))


def describe(method):
    return registry.all_methods()[method][2]


def report(res, by=None):
    period = {"test": "test period", "validation": "validation period", "launch": "launch period (new range)",
              "random": "random split (leaky)"}[res["period"]]
    print(f"Method {res['method']} ({describe(res['method'])}), {period}"
          + (f", settings {res['settings']}" if res["settings"] else ""))
    print(f"Customers scored: {res['customers']:,}{' (quick sample)' if res['quick'] else ''}; "
          f"trained on events before {res['cutoff']}")
    lo, hi = res["recall_ci"]
    print(f"recall@{res['k']} {res['recall']:.3f} (95% interval {lo:.3f} to {hi:.3f}), NDCG@{res['k']} {res['ndcg']:.3f}")
    print(f"coverage {res['coverage']:.1%} of the products on sale")
    print(f"time: fit {res['fit_seconds']:.1f} s, suggestions {res['recommend_seconds']:.1f} s")
