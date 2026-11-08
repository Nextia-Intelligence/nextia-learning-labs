"""route cascade: TF-IDF + logistic regression first; the unsure messages go to the recorded LLM; what the LLM is
not sure about goes to a person.

    route cascade --sure 0.9 --llm-sure 0.8         score these thresholds on the test messages
    route cascade --search                          choose both thresholds on validation, then score test once
"""

import json
from pathlib import Path

from larkroute import costs as cost_table
from larkroute import data, tfidf
from larkroute.cascade import cost, run_cascade, search
from larkroute.llm import ReplayClient
from larkroute.methods import as_proba

ROOT = Path(__file__).resolve().parents[2]


def llm_answers(messages, mode):
    client = ReplayClient(mode)
    a = [client.classify(i) for i in messages["message_id"]]
    return [x["route"] for x in a], [x["confidence"] for x in a], sum(x["usd"] for x in a) / len(a)


def run(args):
    costs = cost_table.load()
    compute = json.loads((ROOT / "config" / "compute.json").read_text())
    first_cost = 0.3 / 1000 / 3600 * compute["usd_per_cpu_hour"]  # about 0.3 ms of computer time a message
    model = tfidf.logistic_regression().fit(data.messages("train")["text"], data.messages("train")["route"])
    if args.search and args.mode == "zero-shot":
        raise SystemExit("The zero-shot answers were recorded for the test messages only, so --search cannot choose "
                         "thresholds on validation. Use the few-shot mode for --search, or give --sure and --llm-sure.")
    sets = {}
    for split in (("validation", "test") if args.search else ("test",)):
        m = data.messages(split)
        proba = as_proba(model.predict_proba(m["text"]), model.classes_).set_index(m.index)
        route, conf, usd = llm_answers(m, args.mode)
        sets[split] = (m, proba, route, conf, usd)
    if args.search:
        m, proba, route, conf, usd = sets["validation"]
        sure, llm_sure, _ = search(m, proba, route, conf, first_cost, usd, costs)
        print(f"Chosen on the validation messages: sure {sure:.2f}, LLM sure {llm_sure:.2f}")
    else:
        sure, llm_sure = args.sure, args.llm_sure
    m, proba, route, conf, usd = sets["test"]
    c = cost(m, run_cascade(proba, route, conf, sure, llm_sure), first_cost, usd, costs)
    print(f"Test messages: {c['first']:.1%} decided by TF-IDF, {c['second']:.1%} by the LLM ({args.mode}, recorded), "
          f"{c['person']:.1%} to a person. Accuracy of the decided messages {c['accuracy_decided']:.1%}.")
    print(f"Cost per 1,000 messages: mistakes and reviews {c['mistakes_and_reviews_per_1000']:.1f} dollars, "
          f"running {c['run_per_1000']:.3f} dollars, total {c['total_per_1000']:.1f} dollars.")


def add(sub):
    p = sub.add_parser("cascade", help="a cheap model first, then the LLM, then a person")
    p.add_argument("--sure", type=float, default=0.9, help="TF-IDF decides when its probability is at least this")
    p.add_argument("--llm-sure", type=float, default=0.0,
                   help="the LLM decides when its stated confidence is at least this")
    p.add_argument("--mode", default="few-shot", choices=["zero-shot", "few-shot"],
                   help="the recorded LLM answers to use (zero-shot: test messages only)")
    p.add_argument("--search", action="store_true", help="choose the two thresholds on validation")
    p.set_defaults(func=run)
