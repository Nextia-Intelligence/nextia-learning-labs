"""Adoption and friction: commands of python -m estate."""




def cmd_adoption(a):
    from estate import adoption

    print(adoption.adoption(a.month, a.bill))


ORDER = 50


def register(sub) -> dict:
    p = sub.add_parser("adoption", help="how far the gateway has spread, and the friction it causes")
    p.add_argument("--month")
    p.add_argument("--bill", action="append", default=[])
    return {"adoption": cmd_adoption}
