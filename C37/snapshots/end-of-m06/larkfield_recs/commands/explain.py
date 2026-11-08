"""recs explain: why item-item CF suggests a product to a customer (which past products, how much each)."""

import numpy as np

from .. import data, registry

NAME = "explain"
HELP = "Explain an item-item suggestion: the customer's products that make the score, and how much each adds."


def add(p):
    p.add_argument("customer", help="a customer ID, for example C100123")
    p.add_argument("--product", help="a product ID (default: the customer's first suggestion)")


def run(args):
    shop = data.load()
    p = data.Period(shop, "test")
    if args.customer not in shop.customer_index:
        raise SystemExit(f"No customer {args.customer}.")
    u = shop.customer_index[args.customer]
    m = registry.make("item-cf", p).fit()
    recs = m.recommend(np.array([u]), 10)[0]
    target = shop.product_index[args.product] if args.product else int(recs[0])
    pr = shop.products
    print(f"{args.customer}: suggestion {shop.product_ids[target]} {pr.title[target]} ({pr.subcategory[target]})")
    h = m.hist[u]
    if h.nnz == 0:
        print("This customer has no events before the test period: the suggestion comes from the trending list.")
        return
    contrib = []
    for j, w in zip(h.indices, h.data):
        s = m.sim[j, target]
        if s:
            contrib.append((w * s, j, w, s))
    total = sum(c[0] for c in contrib)
    if not contrib:
        print("No product of this customer is a neighbour of it: it filled an empty place from the trending list.")
        return
    print(f"score {total:.3f} = sum of (weight of the customer's event x similarity):")
    for c, j, w, s in sorted(contrib, reverse=True)[:8]:
        print(f"  {c:7.3f} = {w:5.2f} x {s:.3f}  {shop.product_ids[j]} {pr.title[j][:50]} ({pr.subcategory[j]})")
