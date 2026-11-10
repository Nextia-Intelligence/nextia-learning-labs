"""search index: build the search indexes."""

from .. import index

NAME = "index"
HELP = "Build the search indexes (SQLite FTS5 and BM25) in outputs/index/."


def add(p):
    pass


def run(args):
    meta = index.build_all()
    print(f"Indexed {meta['products']:,} products in {meta['seconds']} s: SQLite FTS5 (title, description) "
          f"and BM25 (title and description). Index size {index.size_mb():.1f} MB.")
