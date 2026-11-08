"""match weights: m, u and match weights counted on labelled pairs, and the weight of one surname."""

from .. import blocking, fs, vectors

NAME = "weights"
HELP = "Show m, u and the match weight of each agreement level (counted on labelled training pairs)."


def add(p):
    p.add_argument("--field", help="only this field (first, last, email, phone, postcode, street, town, dob)")
    p.add_argument("--surnames", nargs="*", help="the weight of agreeing on these surnames (for example smith)")


def run(args):
    if args.surnames:
        t = fs.surname_weights([s.lower() for s in args.surnames])
        print("Agreeing on one surname (m = 0.95, an assumption; u from how common the surname is):")
        for r in t.itertuples():
            print(f"  {r.surname:<12} {r.records:>6,} records ({r.share:.4%})  u {r.u:.2e}  weight {r.weight:+.2f}")
        return
    v = vectors.get(blocking.DEFAULT["customers"])
    tr = fs.train_pairs(v)
    t = fs.estimate(tr, tr.same)
    if args.field:
        t = t[t.field == args.field]
    print(f"Counted on {len(tr):,} training candidate pairs ({int(tr.same.sum()):,} true pairs):")
    print(t.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
