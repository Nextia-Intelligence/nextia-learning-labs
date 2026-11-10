"""match block: make candidate pairs and measure what the blocking keeps and loses."""

from .. import blocking

NAME = "block"
HELP = "Make the candidate pairs of a blocking (--blocking NAME) and show pair completeness and reduction ratio."


def add(p):
    p.add_argument("--blocking", default="keys")
    p.add_argument("--list", action="store_true", help="list the blockings you can use")


def run(args):
    if args.list:
        for name, (ds, _, desc) in blocking.BLOCKINGS.items():
            print(f"  {name:<18} {ds:<10} {desc}")
        return
    m = blocking.measure(args.blocking, rebuild=True)
    print(f"{args.blocking}: {m['candidates']:,} candidate pairs out of {m['all_pairs']:,} possible pairs "
          f"({m['seconds']} s)")
    print(f"  pair completeness {m['pair_completeness']:.3f} ({m['true_kept']:,} of {m['true_pairs']:,} true pairs "
          f"kept); reduction ratio {m['reduction_ratio']:.6f}")
