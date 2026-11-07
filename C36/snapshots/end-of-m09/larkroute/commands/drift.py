"""route drift: replay the launch month through the current model, week by week, and find new topics.

    route drift                       the weekly table, with the alarms
    route drift --topics --since 2026-02-09    group the unsure messages since that day
"""

from larkroute import data, model_store
from larkroute.drift import route_messages, topics, weekly


def run(args):
    model, card = model_store.load()
    reference = route_messages(model, card, data.messages("validation"))
    stream = route_messages(model, card, data.launch_month())
    if not args.topics:
        table = weekly(stream, reference)
        base = (reference["zone"] != "decide").mean()
        print(f"Model {card['version']}; validation: unsure (review or person) {base:.1%}. Launch month, by week:")
        print(table.to_string(index=False))
        for r in table.itertuples():
            if r.psi >= 0.10 or r.unsure >= 1.5 * base:
                why = [f"route shares moved (PSI {r.psi:.2f})"] if r.psi >= 0.10 else []
                why += [f"unsure messages {r.unsure:.0%}"] if r.unsure >= 1.5 * base else []
                print(f"ALARM week of {r.week}: {' and '.join(why)}. Read a sample of messages before you retrain.")
        return
    unsure = stream[(stream["zone"] != "decide") & (stream["created_at"] >= args.since)]
    table, labels = topics(unsure["text"], k=args.k)
    print(f"{len(unsure)} unsure messages since {args.since}, in {args.k} groups:")
    print(table.to_string(index=False))
    big = table.iloc[0]["group"]
    print("Messages of the largest group:", ", ".join(unsure["message_id"][labels == big].head(5)))


def add(sub):
    p = sub.add_parser("drift", help="replay the launch month: weekly shares, confidence, alarms, new topics")
    p.add_argument("--topics", action="store_true", help="group the unsure messages")
    p.add_argument("--since", default="2026-02-09")
    p.add_argument("--k", type=int, default=6)
    p.set_defaults(func=run)
