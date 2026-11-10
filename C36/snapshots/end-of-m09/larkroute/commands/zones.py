"""route zones: choose the two thresholds (decide / review / send to a person) on the validation messages so that
the review and person zones stay under what the team can carry, then report them once on the test messages."""

import pandas as pd

from larkroute import costs as cost_table
from larkroute import data, tfidf
from larkroute.methods import as_proba
from larkroute.zones import choose, decide, report


def proba_of(model, messages):
    return as_proba(model.predict_proba(messages["text"]), model.classes_).set_index(messages.index)


def messages_per_day(messages) -> float:
    """The labelled messages per day, from the first to the last day of the data."""
    days = pd.to_datetime(messages["created_at"]).dt.normalize()
    return len(messages) / ((days.max() - days.min()).days + 1)


def run(args):
    costs = cost_table.load()
    train, val, test = data.messages("train"), data.messages("validation"), data.messages("test")
    model = tfidf.logistic_regression().fit(train["text"], train["route"])
    high, low, rep_v = choose(val, proba_of(model, val), costs, args.review_max)
    rep = report(test, decide(proba_of(model, test), high, low), costs)
    print(f"Chosen on validation (review and person zones at most {args.review_max:.0%}): "
          f"decide at {high:.2f} or more, send to a person below {low:.2f}.")
    for name, r in (("validation", rep_v), ("test", rep)):
        print(f"{name:>10}: decide {r['decide']:.1%}, review {r['review']:.1%}, person {r['person']:.1%}; "
              f"errors in the decide zone {r['error_rate_decide']:.1%}; "
              f"cost {r['cost_per_1000']:.1f} dollars per 1,000")
    per_day = messages_per_day(data.messages())  # the history: 10,000 messages in 153 days, about 65 a day
    print(f"At about {per_day:.0f} messages a day, the review and person zones are about "
          f"{(rep['review'] + rep['person']) * per_day:.0f} messages a day for Grace's team.")


def add(sub):
    p = sub.add_parser("zones", help="choose the decide / review / person thresholds")
    p.add_argument("--review-max", type=float, default=0.10, help="the largest share of messages that people can read")
    p.set_defaults(func=run)
