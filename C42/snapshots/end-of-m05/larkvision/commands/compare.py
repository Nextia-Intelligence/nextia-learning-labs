"""`vision compare`: the course's comparison table, with your own rows from outputs/table.json."""
from pathlib import Path

from larkvision.compare import Table
from larkvision.paths import data_dir, outputs_dir

TASKS = ["catalogue", "inspect", "count", "match", "attributes"]


def register(sub):
    p = sub.add_parser("compare", help="the comparison table")
    p.add_argument("--task", choices=TASKS, default="catalogue")
    p.add_argument("--setting", help="only rows with this setting, for example 'catalogue test'")
    p.add_argument("--mine", action="store_true", help="only your own rows")
    p.set_defaults(run=run)


def load(data, mine=False):
    rows = [] if mine else Table.load(Path(data) / "comparison_table.json").rows
    own = outputs_dir() / "table.json"
    if own.exists():
        rows += [dict(r, method=r["method"] + " (yours)") for r in Table.load(own).rows]
    return Table(rows)


def run(args):
    t = load(data_dir(args.data), args.mine)
    if args.setting:
        t = Table([r for r in t.rows if r["setting"] == args.setting])
    t.show(args.task)


def add_row(row):
    """Adds one row to outputs/table.json (your own runs)."""
    p = outputs_dir() / "table.json"
    t = Table.load(p) if p.exists() else Table()
    t.add(row)
    t.save(p)
