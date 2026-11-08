"""Safer clustering (Module 7, lesson 2): cut weak links until every cluster passes the checks.

Checks (our choice of rules):
- no two different dates of birth in one entity (a day and month swapped counts as the same date);
- no more than MAX_SIZE records in one entity (no true customer has more than 5 records);
- no pair that a person marked "not the same" (outputs/cannot_link.csv, written by `match undo` and review).
A cluster that fails loses its weakest link (the pair with the lowest score), then the check runs again.
"""

import networkx as nx
import pandas as pd

from . import cluster, prepared
from .paths import out

MAX_SIZE = 6


def cannot_link():
    p = out("cannot_link.csv")
    if not p.exists():
        return set()
    df = pd.read_csv(p, dtype=str)
    return {tuple(sorted(x)) for x in zip(df.record_id_l, df.record_id_r)}


def _dob_conflict(dobs):
    seen = set()
    for d in dobs:
        if not d:
            continue
        swapped = d[:4] + "-" + d[8:10] + "-" + d[5:7]
        if seen and d not in seen and swapped not in seen:
            return True
        seen.add(d)
    return False


def problems(records, dob, banned):
    """Why a cluster fails the checks (an empty list when it passes)."""
    why = []
    if len(records) > MAX_SIZE:
        why.append("too many records")
    if _dob_conflict([dob.get(r, "") for r in records]):
        why.append("two dates of birth")
    rs = set(records)
    if any(a in rs and b in rs for a, b in banned):
        why.append("a person said not the same")
    return why


def safe_components(pairs_df, dataset="customers", log=None):
    """Connected components, then weak links cut until every cluster passes the checks."""
    m = pairs_df[pairs_df["match"] == 1]
    ids = prepared.get(dataset).record_id.tolist()
    base = cluster.components(m, ids)
    dob = dict(zip(prepared.customers().record_id, prepared.customers().dob)) if dataset == "customers" else {}
    banned = cannot_link()
    groups = base.groupby("cluster_id").record_id.apply(list)
    big = [g for g in groups if len(g) > 1 and problems(g, dob, banned)]
    if not big:
        return base
    assign = dict(zip(base.record_id, base.cluster_id))
    member = {r for g in big for r in g}
    edges = m[m.record_id_l.isin(member) & m.record_id_r.isin(member)]
    for g in big:
        gs = set(g)
        e = edges[edges.record_id_l.isin(gs) & edges.record_id_r.isin(gs)]
        G = nx.Graph()
        G.add_nodes_from(g)
        G.add_weighted_edges_from(zip(e.record_id_l, e.record_id_r, e.score))
        stack = [set(c) for c in nx.connected_components(G)]
        while stack:
            comp = stack.pop()
            if len(comp) == 1 or not problems(comp, dob, banned):
                cid = min(comp)
                for r in comp:
                    assign[r] = cid
                continue
            sub = G.subgraph(comp)
            a, b, w = min(sub.edges(data="weight"), key=lambda x: (x[2], x[0], x[1]))
            G.remove_edge(a, b)
            if log is not None:
                log.append({"cut": (a, b), "score": w, "why": problems(comp, dob, banned)})
            stack.extend(set(c) for c in nx.connected_components(G.subgraph(comp)))
    return pd.DataFrame({"record_id": list(assign), "cluster_id": list(assign.values())})
