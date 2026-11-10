"""match active: how many labels does a classifier need? Uncertain pairs first, against random pairs."""

from .. import active

NAME = "active"
HELP = "Simulate active learning: test F1 after each round of labels, for uncertain and for random pairs."


def add(p):
    p.add_argument("--rounds", type=int, default=12)
    p.add_argument("--batch", type=int, default=40)
    p.add_argument("--start", type=int, default=20)


def run(args):
    res = {s: active.simulate(args.rounds, args.start, args.batch, s) for s in ("uncertain", "random")}
    print("Test F1 (threshold: best on validation / 0.5)")
    print(f"{'labels':>7} {'uncertain pairs':>17} {'random pairs':>14}")
    for (n, f_u, g_u), (_, f_r, g_r) in zip(res["uncertain"], res["random"]):
        print(f"{n:>7} {f_u:>8.3f} / {g_u:.3f} {f_r:>7.3f} / {g_r:.3f}")
