"""recs session: next-item suggestions from the current visit."""

from .. import session

NAME = "session"
HELP = "Score next-item suggestions on the test period's visits: Markov transitions, item-item CF and trending."


def add(p):
    pass


def run(args):
    r = session.evaluate()
    print(f"Test period: {r['pairs']:,} moves from one viewed product to the next")
    print(f"{'method':<18}{'hit@10':>8}{'MRR@10':>8}")
    for name in ("markov", "item-cf", "markov+trending", "trending"):
        print(f"{name:<18}{r[name]['hit']:>8.3f}{r[name]['mrr']:>8.3f}")
