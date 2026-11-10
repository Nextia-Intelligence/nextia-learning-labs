"""match forget: a deletion request for one record that is part of a merged entity."""

import pandas as pd

from .. import golden
from ..paths import out

NAME = "forget"
HELP = "Handle a deletion request: remove one record from its entity and rebuild the entity's golden record."


def add(p):
    p.add_argument("record")


def run(args):
    ents = golden.load_entities()
    if ents is None:
        raise SystemExit("No entities yet: run match golden first.")
    row = ents[ents.record_id == args.record]
    if row.empty:
        raise SystemExit(f"No record {args.record!r} in the entities.")
    eid = row.entity_id.iloc[0]
    left = ents[(ents.entity_id == eid) & (ents.record_id != args.record)]
    ents = ents[ents.record_id != args.record]
    golden.save_entities(ents)
    p = out("forgotten.csv")
    pd.DataFrame({"record_id": [args.record]}).to_csv(p, mode="a", header=not p.exists(), index=False)
    g = golden.build(ents)
    g.to_csv(out("golden.csv"), index=False)
    golden.log("forget", record=args.record, entity=eid, records_left=len(left))
    print(f"Removed {args.record} from {eid}; {len(left)} record(s) left in it; its golden record now uses only them.")
    print("Kept: the record ID in outputs/forgotten.csv and the event in the history, with no personal data.")
    print("Not done here: deleting the record from the course data files and from backups (a real system must).")
