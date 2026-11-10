"""`speech agent budget` (the latency budget of each recorded turn) and `speech agent compare` (IVR, agent,
hybrid on the same recorded calls)."""
import json
import statistics
from pathlib import Path

from larkspeech import agent as A
from larkspeech.ivr import replay as R
from larkspeech.paths import data_dir, outputs_dir


def register(sub):
    p = sub.add_parser("agent", help="the voice agent (recorded): latency budget, and IVR vs agent vs hybrid")
    s = p.add_subparsers(dest="agent_command", required=True)
    a = s.add_parser("budget", help="the latency budget of the recorded agent turns")
    a.add_argument("--end-of-turn", type=float, default=0.8)
    a.add_argument("--no-streaming", action="store_true", help="wait for the whole LLM answer and the whole voice")
    a.add_argument("--asr", choices=["base", "tiny"], default="base")
    a.set_defaults(run=run_budget)
    b = s.add_parser("compare", help="IVR, voice agent and hybrid on the same recorded calls")
    b.add_argument("--ivr-records", help="outputs/ivr-replay.jsonl from `speech ivr replay` (default: recorded)")
    b.set_defaults(run=run_compare)


def run_budget(args):
    d = data_dir(args.data)
    _, turns = A.load(d)
    rows = [(p, tot) for _, p, tot in A.input_budgets([t for ts in turns.values() for t in ts], args.end_of_turn,
                                                       not args.no_streaming, f"asr_{args.asr}_s")]
    parts = {k: statistics.median(p[k] for p, _ in rows) for k in rows[0][0]}
    totals = sorted(t for _, t in rows)
    print(f"{len(rows)} caller turns answered by the recorded agent; end of turn {args.end_of_turn} s; "
          f"Whisper {args.asr}; "
          f"{'no streaming' if args.no_streaming else 'streaming'} (recorded LLM times, chat-small)")
    for k, v in parts.items():
        print(f"  {k:24} median {v:5.2f} s  {'#' * int(v * 20)}")
    p90 = totals[int(0.9 * (len(totals) - 1))]
    print(f"  first sound back: median {statistics.median(totals):.2f} s, 90th percentile {p90:.2f} s; "
          f"turns under 1 s: {sum(t < 1 for t in totals)} of {len(totals)}")
    return 0


def run_compare(args):
    d = data_dir(args.data)
    calls, _ = A.load(d)
    if args.ivr_records:
        ivr = [json.loads(x) for x in Path(args.ivr_records).read_text().splitlines() if x]
    else:
        ivr = [json.loads(x) for x in (Path(d) / "recordings/agent/ivr_replay.jsonl").read_text().splitlines() if x]
    costs = json.loads((Path(d) / "costs.json").read_text())
    res = A.design_rows(ivr, calls, costs)
    print(f"{'design':12} {'calls':>5} {'contained':>10} {'to a person':>12} {'wrong actions':>14} {'mean s':>7} "
          f"{'US$ a call':>11}")
    for k, v in res.items():
        print(f"{k:12} {v['calls']:>5} {v['containment']:>10.0%} {v['handover']:>12.0%} {v['wrong_actions']:>14} "
              f"{v['mean_seconds']:>7.1f} {v['usd_per_call']:>11.3f}")
    print("Costs are assumptions (data/costs.json); agent answers and times are recorded (chat-small).")
    R.write_records([{"design": k, **v} for k, v in res.items()], outputs_dir() / "designs.jsonl")
    return 0
