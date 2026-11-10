"""Write the lists that you hand in: the weekly email of every customer and the product page of every product.

Run it in your larkfield-recs folder, after `recs batch <your method>`, with the same two variables:

    export LARKFIELD_DATA=final-data LARKFIELD_OUTPUTS=outputs-final
    recs batch two-stage
    python ../nextia-learning-labs/C37/final/export_lists.py

It uses the project's own code (larkfield_recs, as at the end of Module 9) and writes into final-pack/:
  email.csv    customer_id, place, product_id, source: 10 products for every customer in customers.csv.
               The batch list of the customer, with the rules of rules.toml (as `recs evaluate --rules`), and no
               sensitive product for a shared family inbox (as the service's email surface). A customer with no
               batch list, an opted-out customer or a deleted customer gets the fallback, with the same rules.
  similar.csv  product_id, place, similar_id: 10 products for the page of every product. By default the batch
               neighbours, as the service's /similar answer (item-cf, or content for a product with fewer than 5
               neighbours). --similar cooc|lift|item-cf|content computes them again with that method.
  lists.json   what made the lists: the method, the cut-off, the rules, the counts.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from larkfield_recs import data, registry, serving
from larkfield_recs import rules as rules_mod


def main():
    ap = argparse.ArgumentParser(description="Write final-pack/email.csv and similar.csv from the batch files.")
    ap.add_argument("--out", default="final-pack", help="the folder to write (default final-pack)")
    ap.add_argument("--k", type=int, default=10, help="places in each list (default 10)")
    ap.add_argument("--similar", default="batch", choices=["batch", "cooc", "lift", "item-cf", "content"],
                    help="the product page's method (default batch: the neighbours that recs batch wrote)")
    a = ap.parse_args()
    server = serving.Server()
    if server.meta is None:
        raise SystemExit("No batch lists in outputs. Run `recs batch <method>` first, with the same "
                         "LARKFIELD_DATA and LARKFIELD_OUTPUTS.")
    shop, p, k = server.shop, server.period, a.k
    if shop.n_products < 3000:
        raise SystemExit("This data folder has no Home office products. Set LARKFIELD_DATA=final-data.")
    rules = rules_mod.load()
    sensitive = shop.products.sensitive.to_numpy(dtype=bool)
    cust = shop.customers.set_index("customer_id")
    opted = cust.opted_out.astype(bool).to_dict()
    shared = cust.shared_email.astype(bool).to_dict()
    deleted = data.deleted_customers()

    personal = [c for c in shop.customer_ids if c in server.lists and not opted.get(c) and c not in deleted]
    users = np.array([shop.customer_index[c] for c in personal], dtype=np.int64)
    long = np.array([server.lists[c] for c in personal]) if personal else np.empty((0, 50), int)
    ruled = rules_mod.apply(long, p, rules, k + 5, users=users) if len(users) else long
    fallback = rules_mod.apply(np.array([server.fallback[:50]]), p, rules, k + 5, users=np.array([-1]))[0]

    rows, sources = [], {"model": 0, "fallback": 0}
    lists = dict(zip(personal, ruled))
    for c in shop.customer_ids:
        row, source = (lists[c], "model") if c in lists else (fallback, "fallback")
        items = [int(x) for x in row if x >= 0 and not (shared.get(c) and sensitive[x])]
        if len(items) < k:   # a shared inbox lost a sensitive product: fill from the fallback
            items += [int(x) for x in fallback if x >= 0 and x not in items and not (shared.get(c) and sensitive[x])]
        sources[source] += 1
        for place, x in enumerate(items[:k], 1):
            rows.append((c, place, shop.product_ids[x], source))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=["customer_id", "place", "product_id", "source"]).to_csv(out / "email.csv", index=False)

    srows = []
    if a.similar != "batch":
        model = registry.make(a.similar, p).fit()
        content = model if a.similar == "content" else registry.make("content", p).fit()
    for pid in shop.product_ids:
        if a.similar == "batch":
            items, _ = server.similar(pid, k)
        else:
            i = shop.product_index[pid]
            idx = model.similar(i, 2 * k)[0] if a.similar == "content" else model.neighbours(i, 2 * k)[0]
            if len(idx) < 5:   # too little history: close text instead, as the batch does
                idx = content.similar(i, 2 * k)[0]
            items = server._clean(idx, k)
        srows += [(pid, place, shop.product_ids[x]) for place, x in enumerate(items, 1)]
    pd.DataFrame(srows, columns=["product_id", "place", "similar_id"]).to_csv(out / "similar.csv", index=False)

    meta = {"method": server.meta["method"], "trained_on_events_before": server.meta["trained_on_events_before"],
            "rules": rules, "k": k, "customers": len(shop.customer_ids), "personal_lists": sources["model"],
            "fallback_lists": sources["fallback"], "products": len(shop.product_ids), "similar": a.similar}
    (out / "lists.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(f"Wrote {out}/email.csv: {len(shop.customer_ids):,} customers, {sources['model']:,} personal lists and "
          f"{sources['fallback']:,} fallback lists ({server.meta['method']}, trained on the events before "
          f"{server.meta['trained_on_events_before']})")
    print(f"Wrote {out}/similar.csv: {len(shop.product_ids):,} product pages ({a.similar})")


if __name__ == "__main__":
    main()
