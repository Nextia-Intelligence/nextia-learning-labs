"""match golden: entities with stable IDs and one golden record each."""

from .. import golden, pairs, safecluster

NAME = "golden"
HELP = "Make entities from a run (safe clustering), give them stable IDs and build their golden records."


def add(p):
    p.add_argument("--run", default="lgbm")
    p.add_argument("--show", help="show the golden record and source records of one entity (LK-...)")


def run(args):
    if args.show:
        _show(args.show)
        return
    df = pairs.get(args.run)
    cl = safecluster.safe_components(df, "customers")
    ents = golden.entity_ids(cl, golden.load_entities())
    golden.save_entities(ents)
    g = golden.build(ents)
    g.to_csv(golden.out("golden.csv"), index=False)
    merged = int((g.records > 1).sum())
    golden.log("build", run=args.run, entities=len(g), merged=merged)
    print(f"{len(g):,} entities from {len(ents):,} records ({merged:,} with more than one record); "
          f"{int(g.get('dob_conflict', False).fillna(False).sum())} with two dates of birth")
    print("Saved outputs/entities.csv and outputs/golden.csv")


def _show(eid):
    import pandas as pd

    from .. import data
    if not golden.out("golden.csv").exists():
        raise SystemExit("No golden records yet: run `match golden` first.")
    g = pd.read_csv(golden.out("golden.csv"), dtype=str, keep_default_na=False).set_index("entity_id")
    ents = golden.load_entities()
    if eid not in g.index:
        raise SystemExit(f"No entity {eid!r}.")
    row = g.loc[eid]
    print(f"{eid}: {row['records']} records from {row['sources']}")
    for f in ("name", "email", "phone", "address", "postcode", "dob"):
        src = row.get(f"{f}_from", "") if f != "postcode" else row.get("address_from", "")
        print(f"  {f:<9} {row.get(f, '') or '-':<40} from {src or '-'}")
    recs = data.records().set_index("record_id")
    for rid in sorted(ents[ents.entity_id == eid].record_id):
        r = recs.loc[rid]
        print(f"  {rid}  {r['name']} | {r['email'] or '-'} | {r['phone'] or '-'} | {r['address'] or r['postcode']}")
