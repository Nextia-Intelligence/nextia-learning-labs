"""match bench: time and memory of each matching step."""

from .. import bench

NAME = "bench"
HELP = "Time blocking, comparison vectors, LightGBM and Splink on N records (default: 10,000, 30,000 and all)."


def add(p):
    p.add_argument("--records", type=int, nargs="*", default=[10_000, 30_000, 60_108])


def run(args):
    print(f"{'records':>8} {'candidates':>11} {'block s':>8} {'vectors s':>10} {'lgbm s':>7} {'splink train s':>15} "
          f"{'splink predict s':>17} {'peak MB':>8}")
    for n in args.records:
        r = bench.run(n)
        lg = f"{r['lgbm_s']:.1f}" if r["lgbm_s"] is not None else "-"
        print(f"{r['records']:>8,} {r['candidates']:>11,} {r['block_s']:>8.1f} {r['vectors_s']:>10.1f} {lg:>7} "
              f"{r['splink_train_s']:>15.1f} {r['splink_predict_s']:>17.1f} {r['peak_mb']:>8.0f}")
    print("Peak MB is the most memory this program used so far (it only grows).")
