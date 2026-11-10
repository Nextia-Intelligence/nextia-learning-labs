"""match cluster: join a run's pairs into entities (connected components, or safe clustering)."""

from .. import cluster, data, pairs, safecluster
from ..paths import out

NAME = "cluster"
HELP = "Join the pairs of a run into entities and count them (--method cc: connected components; safe: checked)."


def add(p):
    p.add_argument("--run", default="exact")
    p.add_argument("--method", default="cc", choices=["cc", "safe"])
    p.add_argument("--show-cuts", type=int, default=0, help="safe: show this many links that were cut")


def run(args):
    ds = pairs.dataset(args.run)
    df = pairs.get(args.run)
    cuts = []
    cl = cluster.components(df, pairs.record_ids(ds)) if args.method == "cc" else \
        safecluster.safe_components(df, ds, log=cuts)
    path = out("clusters", f"{args.run}-{args.method}.csv")
    cl.to_csv(path, index=False)
    sizes = cl.groupby("cluster_id").size()
    true_n = data.dataset_truth(ds).entity_id.nunique()
    print(f"{args.run} ({args.method}): {len(cl):,} records -> {len(sizes):,} entities (true: {true_n:,})")
    big = sizes.sort_values(ascending=False).head(3)
    print("Largest clusters: " + ", ".join(f"{cid} ({n} records)" for cid, n in big.items()))
    if args.method == "safe":
        print(f"Links cut: {len(cuts):,}")
        for c in cuts[: args.show_cuts]:
            print(f"  {c['cut'][0]} / {c['cut'][1]}  score {c['score']:.3f}  ({', '.join(c['why'])})")
    print(f"Saved to {path}")
