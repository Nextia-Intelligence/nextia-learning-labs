"""recs loop: read the simulated feedback loop (a recommender that learns only from its own clicks)."""

import pandas as pd

from ..paths import data_dir

NAME = "loop"
HELP = "Read the simulated feedback loop (data/online/feedback_loop.csv): products shown and revenue, with and without exploration."


def add(p):
    p.add_argument("--weeks", action="store_true", help="show every week, not only the summary")


def run(args):
    df = pd.read_csv(data_dir() / "online" / "feedback_loop.csv")
    print("SIMULATED on the course's behaviour model: 12 weeks, the home page learns only from its own log")
    print(f"{'learner':<8}{'exploration':>12}{'products shown in 12 weeks':>28}{'week-1 products still in the top 10':>37}"
          f"{'revenue/visit weeks 1-4':>25}{'weeks 9-12':>12}")
    for (lr, s), g in df.groupby(["learner", "exploration"], sort=False):
        print(f"{lr:<8}{s:>12.0%}{g.products_shown_so_far.iloc[-1]:>28,}{g.top10_same_as_week1.iloc[-1]:>37}"
              f"{g.revenue_per_visit[:4].mean():>25.2f}{g.revenue_per_visit[8:].mean():>12.2f}")
    if args.weeks:
        print(df.to_string(index=False))
