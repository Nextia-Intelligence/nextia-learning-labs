"""`speech wer` (one pair, with the alignment) and `speech score` (recorded transcripts, by slice)."""
from larkspeech import compare as C
from larkspeech import scoring
from larkspeech.paths import data_dir

MARK = {"ok": " ", "sub": "S", "del": "D", "ins": "I"}


def register(sub):
    p = sub.add_parser("wer", help="WER and CER of one transcript against its reference, with the alignment")
    p.add_argument("reference")
    p.add_argument("hypothesis")
    p.add_argument("--level", choices=["none", "basic", "full"], default="full")
    p.add_argument("--language", choices=["en", "fr"], default="en")
    p.set_defaults(run=run_wer)
    q = sub.add_parser("score", help="score a recorded recogniser on the call set, by slice")
    q.add_argument("--method", default="whisper-tiny")
    q.add_argument("--split", default="test")
    q.add_argument("--kind", choices=["phone", "wideband"], default="phone")
    q.add_argument("--by", choices=["language", "line", "noise", "accent", "channels"])
    q.add_argument("--level", choices=["none", "basic", "full"], default="full")
    q.set_defaults(run=run_score)


def run_wer(args):
    r = C.normalise(args.reference, args.level, args.language)
    h = C.normalise(args.hypothesis, args.level, args.language)
    ops = C.align(r.split(), h.split())
    cols = [(a or "", b or "", MARK[op]) for op, a, b in ops]
    w = [max(len(a), len(b), 1) for a, b, _ in cols]
    print("REF: " + " ".join((a or "*" * len(b)).ljust(n) for (a, b, _), n in zip(cols, w)))
    print("HYP: " + " ".join((b or "*" * len(a)).ljust(n) for (a, b, _), n in zip(cols, w)))
    print("     " + " ".join(m.ljust(n) for (_, _, m), n in zip(cols, w)))
    c = C.counts(r, h)
    print(f"{c['sub']} substitutions, {c['del']} deletions, {c['ins']} insertions, {c['ref_words']} reference words: "
          f"WER {C.wer(r, h):.1%}, CER {C.cer(r, h):.1%} (normalisation: {args.level})")
    return 0


def run_score(args):
    res = scoring.score(data_dir(args.data), args.method, args.split, args.kind, args.by, args.level)
    print(f"{args.method}, {args.split} calls, {args.kind} audio, normalisation {args.level}")
    print(f"{'slice':14} {'calls':>5} {'words':>6} {'WER':>7} {'CER':>7} {'order nos wrong':>16} "
          f"{'products wrong':>15}")
    for k, v in res.items():
        o, p = v["important"].get("order", {}), v["important"].get("product", {})
        print(f"{k:14} {v['calls']:>5} {v['words']:>6} {v['wer']:>7.1%} {v['cer']:>7.1%} "
              f"{o.get('missed', 0):>7} of {o.get('items', 0):<6} {p.get('missed', 0):>6} of {p.get('items', 0):<6}")
    return 0
