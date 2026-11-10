"""The golden record (Module 7, lesson 3): one best value per field for each entity, with the record it came from.

Merge rules (survivorship), our choice:
- name: the most common full name in the entity; on a tie, the most trusted source (shop, then loyalty, then
  garden centres);
- email, phone: the newest record that has one (by the record's creation date);
- address and postcode: the newest record that has a street address, else the newest postcode;
- date of birth: the most common one (a day and month swap counts as the same date).
The source records are never changed. Every merge, split and deletion is written to outputs/history.jsonl, so a
merge can be undone. A record in outputs/forgotten.csv (`match forget`, Module 8) is left out of the entities.

`build(entities, records)` works on any table with the prepared columns (record_id, source, created, full, email,
phone, number, street, unit, town, province, postcode, dob), for example the records of another company.
"""

import json
import time
from collections import Counter

import pandas as pd

from . import prepared
from .paths import out

TRUST = {"shop": 0, "loyalty": 1, "garden": 2}


def entity_ids(clusters, previous=None):
    """A stable entity ID for each cluster: LK- and the smallest record ID, or the ID it had before.

    An old ID goes to one cluster only: when a cluster was split, the part with the most records of the old entity
    keeps the ID (on a tie, the part with the smallest record ID), and the other parts get new IDs.
    """
    if previous is not None and len(previous):
        old = dict(zip(previous.record_id, previous.entity_id))
        members = clusters.groupby("cluster_id").record_id.apply(sorted).to_dict()
        have = {cid: Counter(old[r] for r in recs if r in old) for cid, recs in members.items()}
        out_ = {cid: (min(n) if n else f"LK-{cid}") for cid, n in have.items()}   # as before: the smallest old ID
        by_id = {}
        for cid, eid in out_.items():
            by_id.setdefault(eid, []).append(cid)
        taken = set(out_.values())
        for eid, cids in by_id.items():
            if len(cids) < 2:
                continue
            keep = min(cids, key=lambda c: (-have[c][eid], c))
            for cid in cids:
                if cid != keep:
                    free = sorted(e for e in have[cid] if e not in taken)
                    free += [f"LK-{r}" for r in members[cid] if f"LK-{r}" not in taken]
                    out_[cid] = free[0] if free else f"LK-{cid}-{len(taken)}"
                    taken.add(out_[cid])
        return clusters.assign(entity_id=clusters.cluster_id.map(out_))
    return clusters.assign(entity_id="LK-" + clusters.cluster_id)


def forgotten():
    """The record IDs of deletion requests (outputs/forgotten.csv)."""
    p = out("forgotten.csv")
    return set(pd.read_csv(p, dtype=str).record_id) if p.exists() else set()


def without_forgotten(entities):
    gone = forgotten()
    return entities[~entities.record_id.isin(gone)] if gone else entities


def build(entities, records=None, trust=None):
    """entities: record_id, entity_id -> one golden row per entity, with the source record of each field.

    records: the prepared records (default: the course records); trust: source -> rank, 0 the most trusted
    (default: TRUST; a source missing from it is trusted least).
    """
    records = prepared.customers() if records is None else records
    trust = TRUST if trust is None else trust
    p = records.merge(entities[["record_id", "entity_id"]], on="record_id")
    p = p.assign(trust=p.source.map(trust).fillna(len(trust))).sort_values(["entity_id", "created"],
                                                                           ascending=[True, False])
    rows = []
    for eid, g in p.groupby("entity_id", sort=True):
        row = {"entity_id": eid, "records": len(g), "sources": ",".join(sorted(set(g.source)))}
        names = Counter(g.full[g.full != ""])
        if names:
            top = max(names.values())
            cand = g[g.full.isin([n for n, c in names.items() if c == top])].sort_values(["trust", "created"],
                                                                                        ascending=[True, False])
            row["name"], row["name_from"] = cand.full.iloc[0], cand.record_id.iloc[0]
        for f in ("email", "phone"):
            has = g[g[f] != ""]
            row[f], row[f"{f}_from"] = (has[f].iloc[0], has.record_id.iloc[0]) if len(has) else ("", "")
        has = g[g.street != ""]
        if len(has):
            r = has.iloc[0]
            row["address"] = f"{r.number} {r.street}{' unit ' + r.unit if r.unit else ''}, {r.town} {r.province}"
            row["postcode"], row["address_from"] = r.postcode, r.record_id
        else:
            pc = g[g.postcode != ""]
            row["address"], row["postcode"], row["address_from"] = "", (pc.postcode.iloc[0] if len(pc) else ""), \
                (pc.record_id.iloc[0] if len(pc) else "")
        dobs = Counter(d for d in g.dob if d)
        if dobs:
            row["dob"] = dobs.most_common(1)[0][0]
            row["dob_from"] = g[g.dob == row["dob"]].record_id.iloc[0]
            row["dob_conflict"] = len({min(d, d[:4] + "-" + d[8:10] + "-" + d[5:7]) for d in dobs}) > 1
        rows.append(row)
    return pd.DataFrame(rows)


def log(event, **fields):
    with open(out("history.jsonl"), "a") as f:
        f.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": event, **fields}) + "\n")


def history():
    p = out("history.jsonl")
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def save_entities(entities):
    entities[["record_id", "entity_id"]].to_csv(out("entities.csv"), index=False)


def load_entities():
    p = out("entities.csv")
    return pd.read_csv(p, dtype=str) if p.exists() else None


def undo(entities, record_id):
    """Takes one record out of its entity: it becomes a new entity, and it may never join the others again."""
    ent = entities.set_index("record_id").entity_id
    if record_id not in ent.index:
        raise SystemExit(f"No record {record_id!r} in the entities.")
    old = ent[record_id]
    others = ent.index[(ent == old) & (ent.index != record_id)].tolist()
    if not others:
        raise SystemExit(f"{record_id} is alone in {old}: nothing to undo.")
    new_id = f"LK-{record_id}"
    if new_id == old:   # the entity was named after this record: the others get a new name
        new_id, keep = old, f"LK-{min(others)}"
        entities = entities.assign(entity_id=[keep if (e == old and r != record_id) else e
                                              for r, e in zip(entities.record_id, entities.entity_id)])
        old_after = keep
    else:
        entities = entities.assign(entity_id=[new_id if r == record_id else e
                                              for r, e in zip(entities.record_id, entities.entity_id)])
        old_after = old
    p = out("cannot_link.csv")
    rows = pd.DataFrame({"record_id_l": [min(record_id, o) for o in others],
                         "record_id_r": [max(record_id, o) for o in others]})
    rows.to_csv(p, mode="a", header=not p.exists(), index=False)
    log("split", record=record_id, from_entity=old, new_entity=new_id, others_now=old_after)
    return entities, new_id, old_after
