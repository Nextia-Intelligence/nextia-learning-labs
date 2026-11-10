"""`speech vad`: find the speech in calls with energy, WebRTC VAD or Silero VAD, and score it."""
import numpy as np

from larkspeech import data as D
from larkspeech import vad as V
from larkspeech.paths import data_dir


def register(sub):
    p = sub.add_parser("vad", help="find the speech in calls and score it against the true turns")
    p.add_argument("--method", choices=list(V.METHODS), default="silero")
    p.add_argument("--split", default="validation")
    p.add_argument("--by", choices=["noise", "line", "language"], default="noise")
    p.add_argument("--threshold", type=float, help="energy: dB (-40); silero: 0 to 1 (0.5)")
    p.add_argument("--mode", type=int, help="webrtc: 0 to 3 (2)")
    p.add_argument("--limit", type=int, default=0, help="only the first N calls")
    p.set_defaults(run=run)


def run(args):
    d = data_dir(args.data)
    kw = {}
    if args.threshold is not None:
        kw["threshold_db" if args.method == "energy" else "threshold"] = args.threshold
    if args.mode is not None:
        kw["mode"] = args.mode
    calls = D.load_calls(d, args.split, with_audio=True)
    calls = calls[: args.limit] if args.limit else calls
    rows = {}
    V.detect(args.method, np.zeros(16000, np.float32), 16000, **kw)  # load the model before timing
    for c in calls:
        x, sr = D.load_audio(d, c["call_id"], "phone", sr=8000 if args.method != "silero" else 16000)
        regions, dt = V.detect(args.method, x, sr, **kw)
        truth = [(t["start"], t["end"]) for t in c["turns"]]
        s = V.frame_scores(regions, truth, c["duration"])
        rows.setdefault(D.slice_of(c, args.by), []).append((s, dt, c["duration"]))
    print(f"{args.method} {kw or ''} on {len(calls)} {args.split} calls (phone audio)")
    print(f"{args.by:12} {'calls':>5} {'missed speech':>14} {'false speech':>13} {'ms per minute':>14}")
    for k, items in sorted(rows.items()):
        m = np.mean([s["missed"] for s, _, _ in items])
        f = np.mean([s["false"] for s, _, _ in items])
        ms = 1000 * sum(dt for _, dt, _ in items) / (sum(du for _, _, du in items) / 60)
        print(f"{k:12} {len(items):>5} {m:>14.1%} {f:>13.1%} {ms:>14.1f}")
    return 0
