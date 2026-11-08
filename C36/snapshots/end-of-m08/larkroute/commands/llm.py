"""route llm: the recorded LLM answer for one message (route, stated confidence, reason, tokens, cost, time)."""

from larkroute import data
from larkroute.llm import ReplayClient


def run(args):
    m = data.messages()
    row = m[m["message_id"] == args.message_id]
    if row.empty:
        raise SystemExit(f"No message {args.message_id}")
    a = ReplayClient(args.mode).classify(args.message_id)
    r = row.iloc[0]
    print(f"{r['message_id']} ({r['language']}, {r['channel']}): {r['text']}")
    print(f"Label: {r['route']}")
    print(f"Recorded answer of {a['model']} ({args.mode}): {a['route']}, stated confidence {a['confidence']}, "
          f"reason: {a['reason']}")
    print(f"Tokens: {a['tokens_in']} in, {a['tokens_out']} out; cost {a['usd'] * 1000:.3f} dollars per 1,000 such "
          f"messages; {a['latency_s']:.2f} s. (A replayed answer: no call was made.)")


def add(sub):
    p = sub.add_parser("llm", help="show the recorded LLM answer for one message")
    p.add_argument("message_id")
    p.add_argument("--mode", default="few-shot", choices=["zero-shot", "few-shot", "reasoning"])
    p.set_defaults(func=run)
