"""search query: search the catalogue and print the results."""

from .. import data, runs, settings

NAME = "query"
HELP = "Search the catalogue with one run and print the top results."


def add(p):
    p.add_argument("text", help='the query, for example "garden hose"')
    p.add_argument("--run", default="bm25", help="the run to use (search eval --list shows them)")
    p.add_argument("-k", type=int, default=10, help="how many results to show (default 10)")
    p.add_argument("--set", action="append", metavar="NAME=VALUE", help="change a setting of the run (repeatable)")


def find_query_id(text):
    q = data.queries()
    hit = q[q["query"] == text]
    return hit["query_id"].iloc[0] if len(hit) else None


def run(args):
    settings.parse(args.set)
    fn = runs.get(args.run)
    qid = find_query_id(args.text)
    res = fn(args.text, qid, max(args.k, 10))[: args.k]
    cat = data.catalogue().set_index("product_id")
    judged = data.judgments().get(qid, {}) if qid else {}
    label = {2: "exact", 1: "partial", 0: "irrelevant"}
    note = f" (query {qid}: judged results are marked)" if qid else ""
    print(f'{args.run}: "{args.text}" -> {len(res)} results{note}')
    for i, (pid, score) in enumerate(res, 1):
        r = cat.loc[pid]
        stock = "" if r["in_stock"] else "  [out of stock]"
        mark = f"  [{label[judged[pid]]}]" if pid in judged else ("  [not judged]" if qid else "")
        print(f"{i:2}. {pid}  {r['title'][:60]:<60}  {r['product_class'][:24]:<24} {r['price']:>8.2f}{stock}{mark}")
