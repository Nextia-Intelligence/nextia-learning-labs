"""recs similar: the neighbours of one product (people also bought, or close text)."""

import numpy as np

from .. import data, registry

NAME = "similar"
HELP = "Show the products most similar to one product: by co-occurrence, lift, cosine or content."


def add(p):
    p.add_argument("product", help="a product ID, for example P10020")
    p.add_argument("--method", default="item-cf", choices=["cooc", "lift", "item-cf", "content"])
    p.add_argument("--n", type=int, default=10)


def run(args):
    shop = data.load()
    p = data.Period(shop, "test")
    if args.product not in shop.product_index:
        raise SystemExit(f"No product {args.product}.")
    i = shop.product_index[args.product]
    m = registry.make(args.method, p).fit()
    if args.method == "content":
        idx, val = m.similar(i, args.n)
    else:
        idx, val = m.neighbours(i, args.n)
    pr = shop.products
    print(f"{args.product}  {pr.title[i]}  ({pr.subcategory[i]}, {pr.price[i]:.2f} dollars)")
    if len(idx) == 0:
        print("No neighbours: nobody touched this product together with another one before the test period.")
    shared = None
    if args.method != "content":
        b = p.matrix(binary=True).tocsc()
        shared = np.asarray((b[:, [i]].T @ b[:, idx]).todense()).ravel() if len(idx) else []
    for r, (j, v) in enumerate(zip(idx, val), 1):
        extra = f"  shared customers {int(shared[r - 1])}" if shared is not None else ""
        print(f"{r:>3}. {shop.product_ids[j]}  {v:8.3f}  {pr.title[j][:48]:<48} ({pr.subcategory[j]}){extra}")
