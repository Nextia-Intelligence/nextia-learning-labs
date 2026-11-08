"""match daily: match one day of new records against the existing entities."""

from .. import incremental

NAME = "daily"
HELP = "Match the new records of one day (--day 1 to 7) against the entities (run match golden first)."


def add(p):
    p.add_argument("--day", type=int, required=True)


def run(args):
    r = incremental.run_day(args.day)
    print(f"Day {r['day']}: {r['records']} new records: {r['joined']} joined an existing entity, "
          f"{r['new_entities']} started a new entity")
    print(f"  {r['review']} pairs sent to review; {r['two_entities']} record(s) would join two entities "
          f"(not merged alone)")
    print(f"  checked against the true customers: {r['right_joins']} right joins, {r['wrong_joins']} wrong joins, "
          f"{r['missed_known']} new entities for customers we already knew")
