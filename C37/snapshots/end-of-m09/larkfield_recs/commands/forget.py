"""recs forget: apply a customer's deletion request, in the data AND in the model."""

from .. import data, serving
from ..methods.neighbours import item_similarity
from ..paths import outputs_dir

NAME = "forget"
HELP = "Apply a deletion request: remove the customer's events, rebuild the batch, and show that nothing of them is left."

def add(p):
    p.add_argument("customer", help="a customer ID, for example C100123")
    p.add_argument("--method", default="item-cf", help="the method to rebuild (default item-cf: fast)")

def run(args):
    before = data.load()
    if args.customer not in before.customer_index:
        raise SystemExit(f"No customer {args.customer}.")
    u = before.customer_index[args.customer]
    n = int((before.events.c == u).sum())
    sim_before = item_similarity(serving.now_period(before))
    f = outputs_dir() / "deleted.txt"
    gone = data.deleted_customers() | {args.customer}
    f.write_text("\n".join(sorted(gone)) + "\n")
    after = data.load()
    left = int((after.events.c == u).sum())
    print(f"{args.customer}: {n:,} events before; {left} left in the data the project reads (outputs/deleted.txt)")
    sim_after = item_similarity(serving.now_period(after))
    changed = int((abs(sim_after - sim_before) > 1e-9).sum(axis=1).astype(bool).sum())
    print(f"The item-item model changes for {changed:,} products when it is trained again without this customer: "
          f"a model trained before the request still holds their data until it is retrained.")
    meta = serving.build(args.method, after)
    srv = serving.Server(after)
    _items, source, reason = srv.recommend(args.customer)
    print(f"Batch rebuilt ({meta['method']}); {args.customer} is in the lists: {args.customer in srv.lists}; "
          f"their suggestions now come from: {source} ({reason})")
