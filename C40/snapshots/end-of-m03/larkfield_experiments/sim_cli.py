"""The `sim` command: Larkfield's traffic simulator. It knows the true effect of every change."""

import argparse
import time

from .runs import save_run
from .scenarios import all_scenarios


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sim", description="Larkfield's traffic simulator (synthetic data).")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.add_parser("list", help="list the scenarios")
    run = sub.add_parser("run", help="run a scenario and write its data to runs/<scenario>-s<seed>/")
    run.add_argument("--scenario", required=True)
    run.add_argument("--seed", type=int, default=None, help="the random seed (default: the scenario's own)")
    run.add_argument("--customers", type=int, default=None, help="how many customers (default: the scenario's own)")
    about = sub.add_parser("about", help="what a scenario simulates")
    about.add_argument("scenario")
    args = parser.parse_args(argv)
    scenarios = all_scenarios()
    if args.command == "list":
        for name, mod in scenarios.items():
            print(f"{name:<14} {mod.ABOUT}")
    elif args.command == "about":
        mod = _get(scenarios, args.scenario)
        print(f"{mod.NAME}: {mod.ABOUT}\n\n{(mod.__doc__ or '').strip()}")
    elif args.command == "run":
        mod = _get(scenarios, args.scenario)
        seed = mod.DEFAULT_SEED if args.seed is None else args.seed
        t0 = time.time()
        tables, truth, meta = mod.run(seed, args.customers)
        folder = save_run(mod.NAME, seed, tables, truth, meta)
        files = ", ".join(f"{k} ({len(v):,} rows)" for k, v in tables.items())
        print(f"Scenario {mod.NAME} (seed {seed}): {mod.ABOUT}.")
        print(f"Wrote {folder}: {files}. Synthetic data. {time.time() - t0:.1f} s")
    else:
        parser.print_help()


def _get(scenarios, name):
    if name not in scenarios:
        raise SystemExit(f"No scenario '{name}'. Scenarios: {', '.join(scenarios)}")
    return scenarios[name]


if __name__ == "__main__":
    main()
