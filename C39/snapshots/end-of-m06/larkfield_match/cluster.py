"""Join pairs into entities: connected components with a union-find.

If A = B and B = C, the three records become one entity, even when A and C were never compared.
"""

import pandas as pd


def components(pairs, record_ids):
    """record_id -> cluster_id for every record. The cluster ID is the smallest record ID in the cluster."""
    parent = {r: r for r in record_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    m = pairs[pairs["match"] == 1] if "match" in pairs else pairs
    for a, b in zip(m.record_id_l, m.record_id_r):
        ra, rb = find(a), find(b)
        if ra != rb:
            if ra < rb:
                parent[rb] = ra
            else:
                parent[ra] = rb
    ids = list(parent)
    return pd.DataFrame({"record_id": ids, "cluster_id": [find(r) for r in ids]})


def sizes(clusters):
    """How many clusters have each size (size -> count), largest sizes last."""
    return clusters.groupby("cluster_id").size().value_counts().sort_index()
