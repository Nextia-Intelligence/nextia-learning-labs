"""route calibration: is a confidence of 0.9 right 9 times in 10? The reliability table and the expected
calibration error (ECE) of TF-IDF + logistic regression, or of a recorded method's confidence."""

from larkroute import data
from larkroute.methods import available
from larkroute.zones import reliability

DEFAULT = "TF-IDF + logistic regression"


def confidence_and_route(name, messages):
    m = available()[name]()
    if getattr(m, "trains", False):
        m.fit(data.messages("train"))
    if hasattr(m, "confidence"):  # a recorded method: the confidence it gave
        return m.confidence(messages), m.predict(messages)
    p = m.proba(messages)
    return p.max(axis=1).to_numpy(), list(p.idxmax(axis=1))


def run(args):
    msgs = data.messages(args.split)
    conf, route = confidence_and_route(args.method, msgs)
    table, ece = reliability(conf, msgs["route"].to_numpy() == route)
    print(f"{args.method} on the {args.split} messages: expected calibration error {ece:.3f}")
    print(table.to_string(index=False))


def add(sub):
    p = sub.add_parser("calibration", help="the reliability table of a method's confidence")
    p.add_argument("--method", default=DEFAULT)
    p.add_argument("--split", default="validation", choices=["validation", "test"])
    p.set_defaults(func=run)
