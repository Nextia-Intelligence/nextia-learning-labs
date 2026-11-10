"""match show: one record, or every record of one true customer."""

from .. import data

NAME = "show"
HELP = "Show a record (for example S-000001) and the other records of the same true customer."


def add(p):
    p.add_argument("record", help="a record ID (S-, L-, G-) or an entity ID (E-)")


def run(args):
    t = data.truth().set_index("record_id")
    recs = data.records().set_index("record_id")
    if args.record.startswith("E-"):
        eid = args.record
    elif args.record in t.index:
        eid = t.loc[args.record, "entity_id"]
    else:
        raise SystemExit(f"No record {args.record!r}.")
    ids = t.index[t.entity_id == eid].tolist()
    print(f"Entity {eid} ({t.loc[ids[0], 'split']} split): {len(ids)} record(s)")
    cols = ["source", "name", "email", "phone", "address", "postcode", "date_of_birth"]
    for rid in sorted(ids):
        r = recs.loc[rid]
        print(f"  {rid}  " + " | ".join(f"{r[c]}" if r[c] else "-" for c in cols))
    pl = data.planted()
    probs = sorted(set(pl[pl.record_id.isin(ids)].problem))
    if probs:
        print(f"Practice problems we made on purpose: {', '.join(probs)}")
