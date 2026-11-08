"""search explain: each part of the BM25 score of one product for one query."""

import math

import numpy as np

from .. import data, index, text

NAME = "explain"
HELP = "Show each part of the BM25 score of one product for a query: tf, df, IDF and length."


def add(p):
    p.add_argument("query")
    p.add_argument("product_id")
    p.add_argument("--field", default="all", choices=sorted(index.FIELDS))


def parts(query, product_id, field="all", analyzer="plain"):
    """One row per query word: tf, df, idf, the product's length, the average length and the score part."""
    cat = data.catalogue()
    row = int(np.flatnonzero(cat["product_id"].to_numpy() == product_id)[0])
    r = index.bm25(field, analyzer)
    lengths = index.lengths(field, analyzer)
    n, avg = len(lengths), float(lengths.mean())
    words = text.ANALYZERS[analyzer](index.FIELDS[field](cat.iloc[row]))
    out = []
    for w in dict.fromkeys(text.ANALYZERS[analyzer](query)):
        tf = words.count(w)
        df = int(np.count_nonzero(index.scores(w, field, analyzer))) if w in r.vocab_dict else 0
        idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
        norm = index.K1 * (1 - index.B + index.B * lengths[row] / avg)
        out.append({"word": w, "tf": tf, "df": df, "idf": idf, "length": int(lengths[row]), "avg": avg,
                    "part": idf * tf / (tf + norm) if tf else 0.0})
    total = float(index.scores(query, field, analyzer)[row])
    return out, total


def run(args):
    rows, total = parts(args.query, args.product_id, args.field)
    title = data.catalogue().set_index("product_id").loc[args.product_id, "title"]
    print(f'BM25 of {args.product_id} "{title[:60]}" for "{args.query}" (field {args.field}, '
          f"k1 {index.K1}, b {index.B})")
    print(f"{'word':<14}{'tf':>4}{'df':>8}{'IDF':>8}{'length':>8}{'avg':>8}{'part':>8}")
    for r in rows:
        print(f"{r['word']:<14}{r['tf']:>4}{r['df']:>8}{r['idf']:>8.3f}{r['length']:>8}{r['avg']:>8.1f}"
              f"{r['part']:>8.3f}")
    print(f"sum of the parts {sum(r['part'] for r in rows):.3f}; the index's score {total:.3f}")
