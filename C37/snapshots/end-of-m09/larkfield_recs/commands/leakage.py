"""recs leakage: the same methods on a random split and on the time split, side by side."""

from .. import data, harness

NAME = "leakage"
HELP = "Score methods on a random split (the mistake) and on the time split, and show how much the random split inflates."


def add(p):
    p.add_argument("methods", nargs="*", default=["popular", "item-cf", "als"])


def run(args):
    shop = data.load()
    rnd = data.Period(shop, "random")
    tst = data.Period(shop, "test")
    print(f"Random split: {len(rnd.users):,} customers, orders held out at random from the whole log "
          f"(the training data contains the future)")
    print(f"Time split: {len(tst.users):,} customers, the orders of {shop.splits['test'][0]} to {shop.splits['test'][1]}")
    print(f"{'method':<16}{'random split':>14}{'time split':>12}{'random / time':>15}   (recall@10)")
    for m in args.methods:
        r, _, _ = harness.run(m, "random", shop=shop, period_obj=rnd)
        t, _, _ = harness.run(m, "test", shop=shop, period_obj=tst)
        print(f"{m:<16}{r['recall']:>14.3f}{t['recall']:>12.3f}{r['recall'] / t['recall'] - 1:>+14.0%}")
