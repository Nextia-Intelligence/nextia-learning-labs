"""match normalise: one record before and after cleaning."""

from .. import data, prepared

NAME = "normalise"
HELP = "Show one record as its source wrote it and after parsing and normalising (for example G-000002)."


def add(p):
    p.add_argument("record")


def run(args):
    ds = "products" if args.record[:2] in ("NF", "CL") else "customers"
    if ds == "products":
        raw = data.feed("a" if args.record.startswith("NF") else "b").set_index("product_id")
    else:
        src = {"S": "shop", "L": "loyalty", "G": "garden"}[args.record[0]]
        raw = data.source(src).set_index("record_id")
    if args.record not in raw.index:
        raise SystemExit(f"No record {args.record!r}.")
    print("As written:")
    for k, v in raw.loc[args.record].items():
        print(f"  {k:<14} {v!r}")
    print("Prepared:")
    for k, v in prepared.get(ds).set_index("record_id").loc[args.record].items():
        print(f"  {k:<14} {v.item() if hasattr(v, 'item') else v!r}")
