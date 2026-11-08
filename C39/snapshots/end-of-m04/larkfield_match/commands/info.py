"""match info: what is in the course data."""

from .. import data

NAME = "info"
HELP = "Show what is in the customer sources, the supplier feeds and the labels."


def add(p):
    pass


def run(args):
    recs = data.records()
    counts = recs.source.value_counts()
    parts = ", ".join(f"{data.SOURCE_NAMES[s]} {counts[s]:,}" for s in data.SOURCES)
    print(f"Customer records (synthetic): {len(recs):,} in 3 sources: {parts}")
    t = data.truth()
    per = t.groupby("entity_id").size()
    print(f"True customers: {len(per):,} ({len(recs) / len(per):.2f} records per customer); "
          f"{int((per > 1).sum()):,} customers have more than one record, the largest has {per.max()}")
    for s in data.SOURCES:
        cols = [c for c in data.source(s).columns if c != "record_id"]
        print(f"  {data.SOURCE_NAMES[s]}: {', '.join(cols)}")
    fa, fb = data.feed("a"), data.feed("b")
    pt = data.product_truth()
    both = int(pt.groupby("product_entity").size().gt(1).sum())
    print(f"Supplier feeds (synthetic): Northfield Supply {len(fa):,} products, Copperleaf Wholesale {len(fb):,} "
          f"products; {both:,} products are in both feeds")
    lp = data.labelled_pairs()
    print(f"Labelled pairs: {len(lp):,} ({int(lp.label.sum()):,} same, {int((lp.label == 0).sum()):,} different)")
