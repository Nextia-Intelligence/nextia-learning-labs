"""match vector: the comparison vector of one pair."""

import pandas as pd

from .. import data, prepared, vectors

NAME = "vector"
HELP = "Show the comparison vector of two records (for example L-000001 S-012345)."


def add(p):
    p.add_argument("record_l")
    p.add_argument("record_r")


def run(args):
    ds = "products" if args.record_l[:2] in ("NF", "CL") else "customers"
    pair = pd.DataFrame({"record_id_l": [args.record_l], "record_id_r": [args.record_r]})
    v = vectors.for_pairs(pair, ds).iloc[0]
    df = prepared.get(ds).set_index("record_id")
    cols = ["title", "brand", "size", "pack", "gtin"] if ds == "products" else \
        ["full", "email", "phone", "street", "town", "postcode", "dob"]
    for rid in (args.record_l, args.record_r):
        print(f"  {rid}: " + " | ".join(str(df.loc[rid, c]) or "-" for c in cols))
    for f in vectors.fields(ds):
        val = v[f]
        print(f"  {f:<16} {'missing' if pd.isna(val) else f'{val:.3f}'}")
    ent = data.dataset_truth(ds).set_index("record_id").entity_id
    print(f"True answer: {'same' if ent[args.record_l] == ent[args.record_r] else 'different'}")
