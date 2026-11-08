"""match explain: why Splink gives a pair its match weight (a waterfall)."""

from .. import data, splinkmodel

NAME = "explain"
HELP = "Show each field's match weight for two records, from the saved Splink model (match splink first)."


def add(p):
    p.add_argument("record_l")
    p.add_argument("record_r")


def run(args):
    if not splinkmodel.model_path().exists():
        raise SystemExit("No Splink model yet: run match splink first.")
    linker = splinkmodel.load()
    steps, total, prob = splinkmodel.explain(linker, args.record_l, args.record_r)
    running = 0.0
    for name, w, values in steps:
        running += w
        print(f"  {name:<28} {w:+7.2f}  (total {running:+7.2f})  {values}")
    print(f"Match weight {total:+.2f} -> match probability {prob:.4f}")
    ent = data.truth().set_index("record_id").entity_id
    print(f"True answer: {'same' if ent[args.record_l] == ent[args.record_r] else 'different'}")
