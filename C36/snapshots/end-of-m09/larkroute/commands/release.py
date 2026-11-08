"""route release: compare a candidate model with the current one, slice by slice, and make it current only if
it passes. route release --rollback goes back to the version before.

    route release --candidate v2
"""

import pandas as pd

from larkroute import data, model_store
from larkroute.release import check, slices

NEW_ROUTE_RECALL = 0.80


def run(args):
    if args.rollback:
        prev = model_store.MODELS / "previous"
        if not prev.exists():
            raise SystemExit("No previous version to go back to.")
        version = prev.read_text().strip()
        model_store.set_current(version)
        print(f"Rolled back: the current model is {version}.")
        return
    if not args.candidate:
        raise SystemExit("Name the candidate: route release --candidate v2")
    cur_v = model_store.current()
    cur, cur_card = model_store.load(cur_v)
    cand, cand_card = model_store.load(args.candidate)
    test = data.messages("test")
    rows = check(slices(test, cur.predict(test["text"])), slices(test, cand.predict(test["text"])), args.tolerance)
    new_routes = sorted(set(cand_card["routes"]) - set(cur_card["routes"]))
    for r in new_routes:
        lab = pd.read_csv(data.data_dir() / "launch_labels_sample.csv")
        lab = lab[lab["split"] == "check"]
        texts = data.launch_month().set_index("message_id")["text"]
        pred = cand.predict(texts.loc[lab["message_id"]])
        m = (lab["route"] == r).to_numpy()
        recall = float((pred[m] == r).mean())
        rows.append({"slice": f"new route={r} (launch check)", "messages": int(m.sum()), "current": None,
                     "candidate": round(recall, 3), "result": "ok" if recall >= NEW_ROUTE_RECALL else "WORSE"})
    table = pd.DataFrame(rows)
    print(f"Current {cur_v} against candidate {args.candidate} on the test messages "
          f"(a slice fails if it drops more than {args.tolerance:.0%}; "
          "slices under 30 messages are shown, not judged):")
    print(table.to_string(index=False, na_rep="-"))
    failed = table[table["result"] != "ok"]
    if len(failed):
        print(f"NOT RELEASED: {len(failed)} slice(s) got worse. The current model stays {cur_v}.")
        raise SystemExit(1)
    model_store.set_current(args.candidate)
    print(f"RELEASED: the current model is now {args.candidate}. Restart the service to load it.")


def add(sub):
    p = sub.add_parser("release", help="check a candidate model by slice and make it current if it passes")
    p.add_argument("--candidate")
    p.add_argument("--tolerance", type=float, default=0.02)
    p.add_argument("--rollback", action="store_true")
    p.set_defaults(func=run)
