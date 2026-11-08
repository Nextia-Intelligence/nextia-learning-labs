"""recs matrix: the user-item matrix and how empty it is."""

import numpy as np

from .. import data

NAME = "matrix"
HELP = "Build the customer-by-product matrix (sparse) and show how empty it is."


def add(p):
    p.add_argument("--period", default="test", choices=["test", "validation", "launch"],
                   help="use the events before this period (default test)")
    p.add_argument("--weights", default="view=1,basket=3,order=5", help="weight of each event (default view=1,basket=3,order=5)")


def run(args):
    shop = data.load()
    p = data.Period(shop, args.period)
    w = {k: float(v) for k, v in (x.split("=") for x in args.weights.split(","))}
    m = p.matrix(w)
    users = np.asarray((m > 0).sum(axis=1)).ravel()
    items = np.asarray((m > 0).sum(axis=0)).ravel()
    active = users > 0
    print(f"Events before {p.cutoff}: {len(p.train):,}; weights {w}")
    print(f"Matrix: {m.shape[0]:,} customers x {m.shape[1]:,} products, {m.nnz:,} filled cells "
          f"({m.nnz / (m.shape[0] * m.shape[1]):.3%}); memory {(m.data.nbytes + m.indices.nbytes + m.indptr.nbytes) / 1e6:.1f} MB "
          f"sparse, {m.shape[0] * m.shape[1] * 4 / 1e6:,.0f} MB if it were dense")
    print(f"Customers with any event: {active.sum():,}; products per customer: median {np.median(users[active]):.0f}, "
          f"mean {users[active].mean():.1f}")
    o = p.train[p.train.event == "order"].groupby("c").session.nunique()
    vc = o.value_counts().sort_index()
    print("Orders per customer (customers who ordered): " + ", ".join(
        f"{n}: {vc.get(n, 0):,}" for n in range(1, 6)) + f", 6 or more: {vc[vc.index >= 6].sum():,}")
    top = np.sort(items)[::-1]
    print(f"Products: the 1% most touched products have {top[: len(top) // 100].sum() / top.sum():.1%} of the "
          f"filled cells; {(items == 0).sum():,} products have none")
