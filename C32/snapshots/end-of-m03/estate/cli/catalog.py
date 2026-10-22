"""The capability catalog: commands of python -m estate."""

import sys



def cmd_catalog(a):
    from estate import catalog

    cat = catalog.load_catalog(a.file)
    if a.action == "list":
        for name, cap in cat["capabilities"].items():
            m = cap.get("mapping")
            serves = f"{m['primary']['provider']}/{m['primary']['deployment']}" if m else "nothing yet (planned)"
            print(f"{name:<17} {serves:<26} {cap['contract']['purpose']}")
    elif a.action == "show":
        print(catalog.card(cat, a.name))
    else:
        problems = catalog.check(cat)
        print("\n".join(problems) if problems else "The catalog is consistent: every mapping keeps its contract.")
        if problems:
            sys.exit(1)


ORDER = 10


def register(sub) -> dict:
    p = sub.add_parser("catalog", help="list, show or check the capability catalog")
    p.add_argument("action", choices=["list", "show", "check"])
    p.add_argument("name", nargs="?")
    p.add_argument("--file")
    return {"catalog": cmd_catalog}
