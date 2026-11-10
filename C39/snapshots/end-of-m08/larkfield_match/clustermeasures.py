"""Cluster measures (Module 7, lesson 4): judge the entities, not only the pairs.

- cluster pairs: every pair of records inside one cluster (also pairs the matcher never compared) against the
  true pairs;
- exact clusters: a cluster is right only when it holds exactly the records of one true entity;
- B-cubed: for each record, the share of its cluster that belongs to its entity (precision) and the share of
  its entity that is in its cluster (recall), averaged over records.

Measures on a split use the records of that split's entities; the clusters are made from all records.
"""

import pandas as pd

from . import cluster, data, evaluate, pairs


def measures(clusters, dataset="customers", split="test"):
    t = data.dataset_truth(dataset)[["record_id", "entity_id", "split"]]
    df = clusters.merge(t, on="record_id")
    if split != "all":
        keep = df.split == split
    else:
        keep = pd.Series(True, index=df.index)
    c_size = df.groupby("cluster_id").record_id.transform("size")
    e_size = df.groupby("entity_id").record_id.transform("size")
    both = df.groupby(["cluster_id", "entity_id"]).record_id.transform("size")
    b3_p = (both / c_size)[keep].mean()
    b3_r = (both / e_size)[keep].mean()
    # cluster pairs
    cp = df[["record_id", "cluster_id"]].merge(df[["record_id", "cluster_id"]], on="cluster_id", suffixes=("_l", "_r"))
    cp = cp[cp.record_id_l < cp.record_id_r].assign(match=1)
    pm = evaluate.pair_measures(cp, dataset, split)
    # exact clusters (on the clusters that contain a record of the split)
    sub = df[keep]
    cl_sets = df.groupby("cluster_id").record_id.apply(frozenset)
    en_sets = df.groupby("entity_id").record_id.apply(frozenset)
    cl_in = cl_sets[cl_sets.index.isin(sub.cluster_id)]
    en_in = en_sets[en_sets.index.isin(sub.entity_id)]
    en_set = set(en_in.values)
    exact = sum(1 for s in cl_in.values if s in en_set)
    sizes = df.groupby("cluster_id").size()
    return {"bcubed_precision": float(b3_p), "bcubed_recall": float(b3_r),
            "cluster_pair_precision": pm["precision"], "cluster_pair_recall": pm["recall"],
            "exact_cluster_precision": exact / max(len(cl_in), 1), "exact_cluster_recall": exact / max(len(en_in), 1),
            "entities": int(clusters.cluster_id.nunique()), "largest": int(sizes.max()),
            "clusters_over_5": int((sizes > 5).sum())}


def report(pairs_df, dataset, split):
    """Printed by `match eval` from Module 7 on."""
    ids = pairs.record_ids(dataset)
    rows = [("connected components", cluster.components(pairs_df, ids))]
    try:
        from . import safecluster
        rows.append(("safe clustering", safecluster.safe_components(pairs_df, dataset)))
    except ImportError:
        pass
    for name, cl in rows:
        m = measures(cl, dataset, split)
        print(f"  {name}: {m['entities']:,} entities, largest {m['largest']} records, {m['clusters_over_5']} clusters "
              f"over 5 records")
        print(f"    B-cubed precision {m['bcubed_precision']:.3f}, recall {m['bcubed_recall']:.3f}; cluster pairs "
              f"precision {m['cluster_pair_precision']:.3f}, recall {m['cluster_pair_recall']:.3f}; exact clusters "
              f"precision {m['exact_cluster_precision']:.3f}, recall {m['exact_cluster_recall']:.3f}")
