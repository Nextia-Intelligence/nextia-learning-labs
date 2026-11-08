"""match cluster: join a run's pairs into entities (connected components)."""

from .. import cluster, data, pairs
from ..paths import out

NAME = "cluster"
HELP = "Join the pairs of a run into entities and count them (connected components)."


def add(p):
    p.add_argument("--run", default="exact")


def run(args):
    ds = pairs.dataset(args.run)
    df = pairs.get(args.run)
    cl = cluster.components(df, pairs.record_ids(ds))
    path = out("clusters", f"{args.run}.csv")
    cl.to_csv(path, index=False)
    sizes = cl.groupby("cluster_id").size()
    true_n = data.dataset_truth(ds).entity_id.nunique()
    print(f"{args.run}: {len(cl):,} records -> {len(sizes):,} entities (true: {true_n:,})")
    big = sizes.sort_values(ascending=False).head(3)
    print("Largest clusters: " + ", ".join(f"{cid} ({n} records)" for cid, n in big.items()))
    print(f"Saved to {path}")
