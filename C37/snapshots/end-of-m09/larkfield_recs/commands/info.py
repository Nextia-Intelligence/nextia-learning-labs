"""recs info: what is in the shop log."""

from .. import data

NAME = "info"
HELP = "Show what is in the shop log: products, customers, events and the periods."


def add(p):
    pass


def run(args):
    shop = data.load()
    ev, pr = shop.events, shop.products
    counts = ev.event.value_counts()
    orders = ev[ev.event == "order"]
    per = orders.groupby("c").session.nunique()
    print(f"Products: {shop.n_products:,} in {pr.category.nunique()} categories and {pr.subcategory.nunique()} "
          f"subcategories (synthetic)")
    print(f"Customers: {shop.n_customers:,}; {len(per):,} ordered at least once, {(per == 1).sum() / len(per):.0%} "
          f"of them only once")
    print(f"Events: {len(ev):,} ({counts.get('view', 0):,} views, {counts.get('basket', 0):,} basket adds, "
          f"{counts.get('order', 0):,} order lines in {orders.session.nunique():,} orders), "
          f"{ev.ts.min():%Y-%m-%d} to {ev.ts.max():%Y-%m-%d}")
    s = shop.splits
    print(f"Periods: validation {s['validation'][0]} to {s['validation'][1]}, test {s['test'][0]} to {s['test'][1]}")
    if shop.removed:
        print(f"Deletion requests applied: {shop.removed:,} events removed (outputs/deleted.txt)")
    m = data.interaction_matrix(ev, shop.n_customers, shop.n_products)
    print(f"Customer-product pairs with any event: {m.nnz:,} of {shop.n_customers * shop.n_products:,} "
          f"({m.nnz / (shop.n_customers * shop.n_products):.2%} filled)")
