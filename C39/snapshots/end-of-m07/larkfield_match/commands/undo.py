"""match undo: take one record out of its entity (a reviewer found a wrong merge)."""

from .. import golden

NAME = "undo"
HELP = "Split one record out of its entity: it gets a new entity ID and may never join that entity again."

def add(p):
    p.add_argument("record")

def run(args):
    ents = golden.load_entities()
    if ents is None:
        raise SystemExit("No entities yet: run match golden first.")
    ents, new_id, old_after = golden.undo(ents, args.record)
    golden.save_entities(ents)
    g = golden.build(ents)
    g.to_csv(golden.out("golden.csv"), index=False)
    n_old = int((ents.entity_id == old_after).sum())
    print(f"{args.record} is now entity {new_id}; the other {n_old} record(s) stay in {old_after}.")
    print("Recorded in outputs/history.jsonl and outputs/cannot_link.csv (safe clustering will keep them apart).")
