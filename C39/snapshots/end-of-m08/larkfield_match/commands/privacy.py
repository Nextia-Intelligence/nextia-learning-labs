"""match privacy: what hashing and Bloom filter encoding keep and lose, and the frequency attack."""

from .. import evaluate, pairs, prepared, privacy

NAME = "privacy"
HELP = "Compare matching on raw, hashed and encoded values, and show a frequency attack on encoded surnames."

def add(p):
    p.add_argument("--example", nargs=2, default=["Thériault", "Theriault"], help="two values to encode")

def run(args):
    a, b = (prepared.nz.name(x) for x in args.example)
    print(f"{a!r} / {b!r}: hashes {privacy.hashed(a)} / {privacy.hashed(b)} "
          f"({'equal' if privacy.hashed(a) == privacy.hashed(b) else 'different'})")
    ba, bb = privacy.bloom(a), privacy.bloom(b)
    print(f"  Bloom filters: {len(ba)} and {len(bb)} bits set of {privacy.BITS}; Dice {privacy.dice(ba, bb):.3f}")
    for run_name in ("rules", "hashed-rules", "lgbm", "bloom-lgbm"):
        m = evaluate.pair_measures(pairs.get(run_name, quiet=True), "customers", "test")
        print(f"  {run_name:<14} precision {m['precision']:.3f}, recall {m['recall']:.3f}, F1 {m['f1']:.3f}")
    # the attack: an attacker without the key, with a list of common surnames in order (here: from the loyalty
    # members' list, as if it were a public list), guesses the most frequent encoded surnames of the other records
    recs = prepared.customers()
    public = recs[recs.source == "loyalty"]["last"].value_counts().index.tolist()
    enc = privacy.encode(recs[recs.source != "loyalty"])
    guesses, rows = privacy.frequency_attack(enc, public, top=10)
    right = sum(1 for (_, _, name), row in zip(guesses, rows) if privacy.bloom(name) == row)
    print("Frequency attack on the encoded surnames of the shop and garden-centre records:")
    for (rank, n, name), row in zip(guesses, rows):
        ok = "right" if privacy.bloom(name) == row else "wrong"
        print(f"  {rank:>2}. {n:>5} records -> guess {name!r} ({ok})")
    print(f"  {right} of 10 guessed right, without the key")
