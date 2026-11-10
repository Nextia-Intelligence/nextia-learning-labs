"""search clicks: position bias in the synthetic query log."""

import pandas as pd

from .. import clicks, data

NAME = "clicks"
HELP = "Show position bias in the synthetic query log: clicks by position, and examine(k) estimated from it."


def add(p):
    p.add_argument("action", choices=["bias"])


def run(args):
    s = data.searches()
    imp = data.impressions().merge(s[["search_id", "query_id"]], on="search_id")
    j = data.judgments()
    imp["grade"] = [j.get(q, {}).get(p, -1) if q else -1 for q, p in zip(imp["query_id"], imp["product_id"])]
    ctr = clicks.ctr_by_position(imp)
    exact = imp[imp["grade"] == 2].groupby("position")["clicked"].agg(["mean", "size"])
    est = clicks.propensity(imp, None)
    t = pd.DataFrame({"click rate": ctr, "exact shown": exact["size"], "click rate of exact": exact["mean"],
                      "estimated examine(k)": est, "click model examine(k)": clicks.examine(ctr.index)})
    print(f"{len(s):,} searches, {len(imp):,} results shown (synthetic log; click model ETA {clicks.ETA})")
    print(t.to_string(float_format=lambda x: f"{x:.3f}"))
