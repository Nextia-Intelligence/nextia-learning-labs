"""search info: what is in the course data."""

from .. import data

NAME = "info"
HELP = "Show what is in the catalogue, the queries and the query log."


def add(p):
    pass


def run(args):
    cat = data.catalogue()
    q = data.queries()
    s = data.searches()
    fr = int((cat["title_fr"] != "").sum())
    print(f"Catalogue: {len(cat):,} products in {cat['product_class'].nunique():,} product classes; "
          f"{fr:,} with a French title (machine-translated)")
    print(f"In stock: {cat['in_stock'].mean():.1%}; on sale: {cat['on_sale'].mean():.1%} (synthetic)")
    parts = ", ".join(f"{n} {name}" for name, n in q["split"].value_counts().reindex(
        ["train", "validation", "test"]).items())
    langs = q["language"].value_counts()
    print(f"Queries with judgments: {len(q):,} ({parts}); English {langs.get('en', 0)}, French {langs.get('fr', 0)}")
    n_j = sum(len(v) for v in data.judgments().values())
    print(f"Judgments: {n_j:,} (exact, partial or irrelevant)")
    print(f"Query log (synthetic): {len(s):,} searches, {s['query'].nunique():,} different queries, "
          f"{s['date'].min()} to {s['date'].max()}")
