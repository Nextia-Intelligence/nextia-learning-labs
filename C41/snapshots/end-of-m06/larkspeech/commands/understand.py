"""`speech reason` and `speech compliance`: decisions from transcripts, measured against the labels."""
from collections import Counter

from larkspeech import data as D
from larkspeech import scoring
from larkspeech import understand as U
from larkspeech.paths import data_dir


def register(sub):
    p = sub.add_parser("reason", help="why did they call? rules, a classifier and a recorded LLM")
    p.add_argument("--transcripts", default="reference", help="reference, or a recorded recogniser (whisper-small)")
    p.add_argument("--split", default="test")
    p.set_defaults(run=run_reason)
    q = sub.add_parser("compliance", help="did the agent say the recording notice? exact and fuzzy search")
    q.add_argument("--transcripts", default="reference")
    q.add_argument("--split", default="test")
    q.set_defaults(run=run_compliance)


def texts(d, calls, source, speaker=None):
    if source == "reference":
        return {c["call_id"]: D.reference(c, speaker) for c in calls}
    if speaker:
        raise SystemExit("one speaker's turns exist only for the reference transcripts")
    rec = scoring.load_transcripts(d, source)
    return {c["call_id"]: rec[(c["call_id"], "phone")]["text"] for c in calls if (c["call_id"], "phone") in rec}


def run_reason(args):
    d = data_dir(args.data)
    train = D.load_calls(d, "train")
    calls = D.load_calls(d, args.split, with_audio=args.transcripts != "reference")
    tx = texts(d, calls, args.transcripts)
    calls = [c for c in calls if c["call_id"] in tx]
    clf = U.ReasonClassifier().fit([D.reference(c) for c in train], [c["reason"] for c in train])
    preds = {"keyword rules": [U.rule_reason(tx[c["call_id"]], c["language"]) for c in calls],
             "classifier (TF-IDF)": clf.predict([tx[c["call_id"]] for c in calls])}
    llm_name = f"reason-{args.transcripts}"
    try:
        rec = U.load_llm(d, llm_name)
        preds["LLM (recorded, chat-small)"] = [rec[c["call_id"]]["answer"].get("reason") for c in calls]
    except FileNotFoundError:
        pass
    truth = [c["reason"] for c in calls]
    print(f"Call reason on {len(calls)} {args.split} calls, transcripts: {args.transcripts}")
    for name, p in preds.items():
        acc = sum(a == b for a, b in zip(p, truth)) / len(truth)
        worst = Counter((t, q) for t, q in zip(truth, p) if t != q).most_common(1)
        tail = f"; most common mistake {worst[0][0][0]} -> {worst[0][0][1]} ({worst[0][1]})" if worst else ""
        print(f"  {name:28} accuracy {acc:.1%}{tail}")
    return 0


def run_compliance(args):
    d = data_dir(args.data)
    calls = D.load_calls(d, args.split, with_audio=args.transcripts != "reference")
    if args.transcripts == "reference":
        tx = texts(d, calls, "reference", "agent")
    else:
        tx = texts(d, calls, args.transcripts)
    calls = [c for c in calls if c["call_id"] in tx]
    truth = [c["notice"] != "missing" for c in calls]
    print(f"Recording notice on {len(calls)} {args.split} calls ({sum(truth)} said it, {len(truth) - sum(truth)} "
          f"did not), transcripts: {args.transcripts}")
    for name, f in (("exact phrase", U.notice_exact), ("fuzzy match", U.notice_fuzzy)):
        p = [f(tx[c["call_id"]], c["language"]) for c in calls]
        tp = sum(a and b for a, b in zip(p, truth))
        fa = sum(a and not b for a, b in zip(p, truth))
        print(f"  {name:14} found {tp} of {sum(truth)} notices (recall {tp / max(sum(truth), 1):.1%}); "
              f"false alarms {fa} (a call without the notice marked as compliant)")
    return 0
