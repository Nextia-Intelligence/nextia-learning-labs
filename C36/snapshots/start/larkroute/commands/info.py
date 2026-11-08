"""route info: what is in the data folder, and whether every file is the right one."""

from larkroute import data


def run(args):
    bad = data.check()
    if bad:
        raise SystemExit(f"These data files are missing or changed: {', '.join(bad)}. Run: route reset")
    m = data.messages()
    print(f"{len(m)} messages ({', '.join(f'{n} {s}' for s, n in m['split'].value_counts().items())}), "
          f"from {m['created_at'].min()[:10]} to {m['created_at'].max()[:10]}. All synthetic.")
    print("Routes:", ", ".join(f"{r} {n}" for r, n in m["route"].value_counts().items()))
    print("Languages:", ", ".join(f"{r} {n}" for r, n in m["language"].value_counts().items()),
          "| Channels:", ", ".join(f"{r} {n}" for r, n in m["channel"].value_counts().items()))


def add(sub):
    p = sub.add_parser("info", help="show the data and check its checksums")
    p.set_defaults(func=run)
