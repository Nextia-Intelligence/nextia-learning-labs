"""match similar: every string measure and sound code for two values."""

from .. import similarity
from ..normalise import name as norm_name

NAME = "similar"
HELP = "Score two values with Levenshtein, Jaro-Winkler and token set ratio, and show their sound codes."


def add(p):
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--raw", action="store_true", help="do not normalise the two values first")


def run(args):
    a, b = (args.a, args.b) if args.raw else (norm_name(args.a), norm_name(args.b))
    print(f"{a!r} / {b!r}")
    print(f"  levenshtein distance {similarity.levenshtein_distance(a, b)}")
    for k, fn in similarity.MEASURES.items():
        print(f"  {k:<16} {fn(a, b):.3f}")
    for k, fn in similarity.CODES.items():
        ca, cb = fn(a), fn(b)
        print(f"  {k:<16} {ca} / {cb}  {'same' if ca == cb else 'different'}")
